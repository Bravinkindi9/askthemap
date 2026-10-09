"""POST /api/chat — conversational map assistant endpoint.

Nearby questions use OpenStreetMap counts. Visual questions use Sentinel-2
imagery, with a vision model used only when an API key is configured.
"""
import base64
import io
import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.llm import get_text_llm
from app.models import ChatRequest, ChatResponse, ImageMetadata
from app.osm import nearby_feature_counts
from app.routers.query import _run_stage, query_semaphore
from app.vlm import get_vlm
from geo import fetch_image, search_imagery

router = APIRouter()
logger = logging.getLogger(__name__)

GEOGRAPHIC_SOURCES = ["OpenStreetMap"]
VISUAL_SOURCES = ["Microsoft Planetary Computer (Sentinel-2)"]


def _is_visual_question(question: str) -> bool:
    terms = (
        "satellite", "imagery", "image", "land cover", "vegetation", "forest",
        "built-up", "built up", "visible", "what does it look like", "green space",
    )
    normalized = question.casefold()
    return any(term in normalized for term in terms)


def _has_active_model_key() -> bool:
    if settings.vlm_provider == "openrouter":
        return bool(settings.openrouter_api_key)
    if settings.vlm_provider == "gemini":
        return bool(settings.gemini_api_key)
    return False


def _scene_only_response(metadata: ImageMetadata, image_base64: str, note: str) -> ChatResponse:
    date = metadata.datetime[:10] if metadata.datetime else "an unknown date"
    cloud = (
        f" Scene cloud cover is {metadata.cloud_cover:.0f}%."
        if metadata.cloud_cover is not None else ""
    )
    return ChatResponse(
        reply=(
            f"I found a Sentinel-2 image dated {date}.{cloud} The image is shown below "
            f"for inspection, but {note}."
        ),
        sources=VISUAL_SOURCES,
        evidence=[f"Scene: {metadata.item_id}", f"Acquisition date: {date}"],
        image_metadata=metadata,
        image_base64=image_base64,
    )


async def _nearby_answer(req: ChatRequest) -> ChatResponse:
    radius = settings.overpass_radius_m
    counts = await _run_stage(
        nearby_feature_counts(req.location.lat, req.location.lon),
        stage="overpass_query",
        timeout_s=settings.overpass_timeout_s + 2,
        timeout_detail="The nearby map data request took too long. Please try again.",
        error_detail="OpenStreetMap nearby data is temporarily unavailable. Please try again.",
    )
    evidence = [f"{count:,} {label} within {radius} m" for label, count in counts.items()]
    place = req.location.label or f"{req.location.lat:.4f}, {req.location.lon:.4f}"
    reply = f"Around {place}, OpenStreetMap currently maps " + ", ".join(evidence) + "."
    reply += " Counts are mapped OSM elements, so completeness varies by area."
    return ChatResponse(reply=reply, sources=GEOGRAPHIC_SOURCES, evidence=evidence)


async def _geographic_answer(req: ChatRequest) -> ChatResponse:
    """Use an optional text model, or explain the no-key capabilities."""
    if not _has_active_model_key():
        return ChatResponse(
            reply=(
                "I can verify nearby mapped features without an AI key. Try asking "
                "what roads, buildings, amenities, or water features are nearby."
            ),
            sources=GEOGRAPHIC_SOURCES,
        )
    from app.llm.prompts import build_chat_prompt
    prompt = build_chat_prompt(
        location=req.location,
        history=req.history,
        question=req.question,
    )
    llm = get_text_llm()
    reply = await _run_stage(
        llm.answer(prompt),
        stage="text_llm",
        timeout_s=settings.vlm_timeout_s,
        timeout_detail="The geographic answer took too long. Please try again.",
        error_detail="Could not generate a geographic answer right now. Please try again.",
    )
    return ChatResponse(reply=reply.strip(), sources=GEOGRAPHIC_SOURCES)


async def _visual_answer(req: ChatRequest) -> ChatResponse | None:
    """Return the selected Sentinel-2 scene and optionally explain it with a VLM."""
    stac_result = await _run_stage(
        search_imagery(
            lat=req.location.lat,
            lon=req.location.lon,
            max_cloud_cover=settings.max_cloud_cover,
            stac_api_url=settings.stac_api_url,
            timeout_s=settings.stac_timeout_s,
        ),
        stage="stac_search",
        timeout_s=settings.stac_timeout_s,
        timeout_detail="Searching for satellite imagery took too long. Please try again.",
        error_detail="We couldn't search for satellite imagery right now. Please try again.",
    )
    if stac_result is None:
        return None

    async with query_semaphore:
        image = await _run_stage(
            fetch_image(
                asset_href=stac_result["asset_href"],
                lat=req.location.lat,
                lon=req.location.lon,
                size_px=settings.image_size_px,
                timeout_s=settings.image_fetch_timeout_s,
            ),
            stage="image_fetch",
            timeout_s=settings.image_fetch_timeout_s,
            timeout_detail="Downloading the satellite image took too long. Please try again.",
            error_detail="We found imagery but couldn't download it. Please try again.",
        )

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode("ascii")

    metadata = ImageMetadata(
        item_id=stac_result["id"],
        datetime=stac_result["datetime"],
        cloud_cover=stac_result.get("cloud_cover"),
        collection=stac_result["collection"],
        source="Microsoft Planetary Computer",
        platform=stac_result.get("platform"),
        instrument=stac_result.get("instrument"),
        resolution_m=stac_result.get("resolution_m"),
    )
    if not _has_active_model_key():
        return _scene_only_response(
            metadata,
            image_base64,
            "I cannot reliably interpret its contents without an AI vision provider",
        )

    # Build an enhanced VLM prompt that includes location label and conversation history
    from app.vlm.prompts import build_analyst_prompt
    place = req.location.label or f"{req.location.lat:.4f}, {req.location.lon:.4f}"
    history_suffix = ""
    if req.history:
        lines = [f"{'User' if t.role == 'user' else 'Askio'}: {t.content}" for t in req.history]
        history_suffix = "\n\nConversation so far:\n" + "\n".join(lines)
    full_prompt = build_analyst_prompt(req.location.lat, req.location.lon, req.question)
    full_prompt += f"\nPlace: {place}{history_suffix}"

    vlm = get_vlm()
    try:
        analysis = await _run_stage(
            vlm.ask(image=image, question=full_prompt, lat=req.location.lat, lon=req.location.lon),
            stage="vlm_analysis",
            timeout_s=settings.vlm_timeout_s,
            timeout_detail="The satellite analysis took too long. Please try again.",
            error_detail="The satellite analysis failed. Please try again.",
        )
    except HTTPException:
        logger.warning("Vision provider failed; returning the scene and metadata only")
        return _scene_only_response(
            metadata,
            image_base64,
            "the vision provider is unavailable, so I cannot reliably interpret its contents",
        )

    # Compose a natural conversational reply from the structured analysis
    reply_parts = [analysis.summary]
    if analysis.detail:
        reply_parts.append(analysis.detail)
    if analysis.caveats:
        caveats_text = "; ".join(analysis.caveats)
        reply_parts.append(f"Note: {caveats_text}.")
    reply = " ".join(reply_parts)

    return ChatResponse(
        reply=reply,
        sources=VISUAL_SOURCES,
        image_metadata=metadata,
        image_base64=image_base64,
    )


@router.post("/api/chat", response_model=ChatResponse)
async def chat_with_map(req: ChatRequest):
    question = req.question.casefold()
    nearby_terms = ("nearby", "near me", "around here", "around this", "close to", "within")
    if any(term in question for term in nearby_terms):
        return await _nearby_answer(req)

    path = "visual" if _is_visual_question(req.question) else "geographic"
    logger.info("Chat request classified as '%s' for lat=%.4f lon=%.4f", path, req.location.lat, req.location.lon)

    if path == "visual":
        try:
            result = await _visual_answer(req)
        except HTTPException as exc:
            if exc.status_code == 504:
                raise  # propagate timeouts
            logger.warning("Visual path failed (status=%s)", exc.status_code)
            return ChatResponse(
                reply=(
                    "I couldn't retrieve satellite imagery for this point right now. "
                    "Please try again later."
                ),
                sources=VISUAL_SOURCES,
            )

        if result is not None:
            return result
        return ChatResponse(
            reply=(
                "I couldn't find a recent Sentinel-2 image with acceptable cloud cover "
                "for this point, so I can't answer a visual question from imagery right now."
            ),
            sources=VISUAL_SOURCES,
        )

    return await _geographic_answer(req)
