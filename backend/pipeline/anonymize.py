"""anonymize.py — Anonymize page identifiers for public output (SPECS §11).

Salted SHA-256 hashing, truncated to a configurable length.
"""

from __future__ import annotations

import hashlib

import pandas as pd

from app.core.config import ANON_SALT, load_params


def anonymize_page_id(page_id: str) -> str:
    """Hash a page_id with a salt to produce an anonymized identifier.

    Format: P-{truncated_hex}  (e.g., P-3fa9c1b2ef)
    """
    params = load_params()
    prefix = params["anonymize"]["prefix"]
    length = params["anonymize"]["hash_length"]

    salted = f"{ANON_SALT}:{page_id}"
    hashed = hashlib.sha256(salted.encode()).hexdigest()[:length]
    return f"{prefix}{hashed}"


def anonymize_dataframe(df: pd.DataFrame, id_col: str = "page_id") -> pd.DataFrame:
    """Replace page IDs with anonymized versions throughout a DataFrame.

    Works on both index and column values.
    """
    df = df.copy()

    if id_col in df.columns:
        df[id_col] = df[id_col].apply(anonymize_page_id)
    elif df.index.name == id_col:
        df.index = pd.Index([anonymize_page_id(str(pid)) for pid in df.index], name=id_col)

    return df
