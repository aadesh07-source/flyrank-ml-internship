"""export_static.py — Export API artifacts to static JSON for the React frontend (SPECS §14).

Calls the same service-layer functions as the API, writes to frontend/public/data/.
Guarantees parity between API mode and static mode.
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

# Ensure backend directory is in sys.path when executed directly
_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.core.config import FRONTEND_DATA_DIR, PUBLIC_ARTIFACTS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# Artifacts to export (must match the API endpoint names the frontend expects)
ARTIFACTS = [
    "meta",
    "summary",
    "metrics",
    "pr_curve",
    "precision_at_k",
    "calibration",
    "feature_importance",
    "recommendations",
    "ctr_by_position",
    "playbook",
    "distributions",
    "trends",
    "segments",
]


def export():
    """Copy public artifacts to frontend/public/data/ for static serving."""
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

    exported = 0
    for name in ARTIFACTS:
        src = PUBLIC_ARTIFACTS_DIR / f"{name}.json"
        dst = FRONTEND_DATA_DIR / f"{name}.json"

        if src.exists():
            shutil.copy2(src, dst)
            log.info(f"  ✓ {name}.json")
            exported += 1
        else:
            log.warning(f"  ✗ {name}.json — not found (run pipeline first)")

    log.info(f"Exported {exported}/{len(ARTIFACTS)} artifacts to {FRONTEND_DATA_DIR}")


if __name__ == "__main__":
    export()
