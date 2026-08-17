import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "packages"))
sys.path.insert(0, str(root / "apps" / "api"))

import pytest


@pytest.fixture(autouse=True)
def clear_rate_limit_buckets():
    from app.main import rate_limit_buckets

    rate_limit_buckets.clear()
    yield
    rate_limit_buckets.clear()
