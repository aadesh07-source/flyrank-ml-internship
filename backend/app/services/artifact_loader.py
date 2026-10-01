"""Artifact loader — reads pre-computed JSON artifacts for serving by the API.

The service layer loads from artifacts/public/*.json.  export_static.py calls
the same functions and writes to frontend/public/data/<endpoint>.json,
guaranteeing parity between API and static modes (SPECS §12).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import PUBLIC_ARTIFACTS_DIR


@lru_cache(maxsize=32)
def load_artifact(name: str) -> dict:
    """Load a named public artifact JSON file.

    Args:
        name: artifact key, e.g. 'meta', 'summary', 'recommendations'.
              Maps to ``artifacts/public/{name}.json``.

    Returns:
        Parsed dict from the JSON file, or an error dict if not found.
    """
    path = PUBLIC_ARTIFACTS_DIR / f"{name}.json"
    if not path.exists():
        return {"error": f"Artifact '{name}' not found. Run the pipeline first."}
    with open(path) as f:
        return json.load(f)


def invalidate_cache() -> None:
    """Clear the artifact cache (call after pipeline re-run)."""
    load_artifact.cache_clear()
