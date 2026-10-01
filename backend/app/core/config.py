"""Core configuration — loads env vars & config files for the backend."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
import yaml

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[3]          # repo root
load_dotenv(ROOT_DIR / ".env")
CONFIG_DIR = ROOT_DIR / "config"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
PUBLIC_ARTIFACTS_DIR = ARTIFACTS_DIR / "public"
RAW_ARTIFACTS_DIR = ARTIFACTS_DIR / "raw"
FRONTEND_DATA_DIR = ROOT_DIR / "frontend" / "public" / "data"

# ── Environment ────────────────────────────────────────────────────────────────
HF_TOKEN: str | None = os.getenv("HF_TOKEN")
ANON_SALT: str = os.getenv("ANON_SALT", "capstone-default-salt")


@lru_cache(maxsize=1)
def load_params() -> dict:
    """Load params.yaml — cached for the lifetime of the process."""
    with open(CONFIG_DIR / "params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_schema() -> dict:
    """Load schema.yaml — cached for the lifetime of the process."""
    with open(CONFIG_DIR / "schema.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
