"""scan_public.py — Privacy scanner for exported JSON files (SPECS §11).

Fails if any output JSON contains forbidden patterns: URLs, domains, emails,
or blocklist terms. Run before every commit and in CI.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

# Ensure backend directory is in sys.path when executed directly
_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.core.config import FRONTEND_DATA_DIR, PUBLIC_ARTIFACTS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# Patterns that must NOT appear in public output
FORBIDDEN_PATTERNS = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"www\.", re.IGNORECASE),
    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}", re.IGNORECASE),  # emails
]

# Add custom blocklist terms here (client names, domains, etc.)
BLOCKLIST: list[str] = [
    # "client-name",
    # "example.com",
]


def scan_file(path: Path) -> list[str]:
    """Scan a single JSON file for forbidden content.

    Returns:
        List of violation descriptions (empty = clean).
    """
    violations = []
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        violations.append(f"Could not read {path.name}: {e}")
        return violations

    for pattern in FORBIDDEN_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            # Exception: flyrank.ai link in acknowledgments is allowed
            clean_matches = [m for m in matches if "flyrank.ai" not in m.lower()]
            if clean_matches:
                violations.append(
                    f"{path.name}: Forbidden pattern '{pattern.pattern}' found {len(clean_matches)}x"
                )

    for term in BLOCKLIST:
        if term.lower() in content.lower():
            violations.append(f"{path.name}: Blocklist term '{term}' found")

    return violations


def scan_all() -> bool:
    """Scan all public JSON files.

    Returns:
        True if clean, False if violations found.
    """
    dirs = [PUBLIC_ARTIFACTS_DIR, FRONTEND_DATA_DIR]
    all_violations = []

    for d in dirs:
        if not d.exists():
            continue
        for json_file in d.glob("*.json"):
            violations = scan_file(json_file)
            all_violations.extend(violations)

    if all_violations:
        log.error(f"❌ PRIVACY SCAN FAILED — {len(all_violations)} violation(s):")
        for v in all_violations:
            log.error(f"  • {v}")
        return False

    log.info("✅ Privacy scan passed — no forbidden content found.")
    return True


if __name__ == "__main__":
    clean = scan_all()
    sys.exit(0 if clean else 1)
