"""Prompt builders for the conversational chat endpoint."""
from __future__ import annotations

import unicodedata

from app.models import ChatTurn, LocationContext


def _sanitize(text: str) -> str:
    """Strip control characters from user-supplied text before inserting into prompts."""
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t")


def build_classifier_prompt(question: str) -> str:
    """Return a prompt that asks the model to classify the question as
    'visual' (needs satellite imagery) or 'geographic' (can be answered
    from geographic knowledge alone).
    """
    q = _sanitize(question)
    return (
        "Classify the following map-related question. "
        "Answer with exactly one word: 'visual' if the question requires "
        "analysing a satellite image to answer well (e.g. land cover, "
        "visible structures, vegetation, built-up area), or 'geographic' "
        "if it can be answered from geographic/factual knowledge "
        "(e.g. country, city name, population, history, roads, services).\n\n"
        f"Question: {q}\n\n"
        "Answer:"
    )


def build_chat_prompt(
    location: LocationContext,
    history: list[ChatTurn],
    question: str,
) -> str:
    """Build the main geographic text prompt for a non-visual question."""
    place = location.label or f"{location.lat:.4f}, {location.lon:.4f}"
    zoom_note = f"Map zoom level: {location.zoom}" if location.zoom else ""

    history_block = ""
    if history:
        lines = []
        for turn in history:
            prefix = "User" if turn.role == "user" else "Askio"
            lines.append(f"{prefix}: {_sanitize(turn.content)}")
        history_block = "\n".join(lines)

    q = _sanitize(question)

    parts = [
        "You are Askio, a conversational map assistant.",
        "The user is exploring a map and asking questions about the selected location.",
        "",
        "Active location:",
        f"  Place: {place}",
        f"  Coordinates: {location.lat:.4f}\u00b0, {location.lon:.4f}\u00b0",
    ]
    if zoom_note:
        parts.append(f"  {zoom_note}")

    if history_block:
        parts += ["", "Conversation so far:", history_block]

    parts += [
        "",
        f"User: {q}",
        "",
        "Answer helpfully and honestly. Focus on what you know about this location.",
        "If you are unsure about something, say so clearly rather than inventing facts.",
        "Keep your answer concise (2-4 sentences) unless more detail is clearly needed.",
        "Do not mention that you are an AI or describe your own limitations unless directly asked.",
        "",
        "Askio:",
    ]
    return "\n".join(parts)
