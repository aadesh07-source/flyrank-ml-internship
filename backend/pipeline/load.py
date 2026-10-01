"""load.py — Load FlyRank data from Hugging Face via DuckDB over hf:// paths.

Reads schema.yaml for table paths and column names. Uses HF_TOKEN from env.
"""

from __future__ import annotations

import duckdb
import pandas as pd

from app.core.config import HF_TOKEN, load_schema


def _hf_connection() -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection with the Hugging Face httpfs extension configured."""
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    if HF_TOKEN:
        con.execute(f"""
            CREATE SECRET hf_token (
                TYPE HUGGINGFACE,
                TOKEN '{HF_TOKEN}'
            );
        """)
    return con


def load_search_performance(
    start_date: str | None = None,
    end_date: str | None = None,
    client_id: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Load search performance data (page × date) from fact_content_daily_performance.

    Filters to rows where gsc_data_available is True and gsc_impressions > 0.
    """
    schema = load_schema()
    table_cfg = schema["tables"]["fact_content_daily_performance"]
    hf_path = table_cfg["hf_path"]
    cols = table_cfg["columns"]

    con = _hf_connection()
    where_clauses = [
        f"{cols['gsc_data_available']} = true",
        f"{cols['impressions']} > 0",
    ]
    if start_date:
        where_clauses.append(f"{cols['report_date']} >= '{start_date}'")
    if end_date:
        where_clauses.append(f"{cols['report_date']} <= '{end_date}'")
    if client_id:
        where_clauses.append(f"{cols['client_id']} = '{client_id}'")

    where_sql = " AND ".join(where_clauses)
    limit_sql = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT
            {cols['content_id']}   AS page_id,
            {cols['report_date']}  AS date,
            {cols['client_id']}    AS client_id,
            {cols['impressions']}  AS impressions,
            {cols['clicks']}       AS clicks,
            {cols['avg_position']} AS avg_position
        FROM read_parquet('{hf_path}')
        WHERE {where_sql}
        {limit_sql}
    """
    df = con.execute(query).fetchdf()
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_engagement(
    start_date: str | None = None,
    end_date: str | None = None,
    client_id: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Load engagement data (page × date) from fact_content_daily_performance.

    Filters to rows where ga4_data_available is True.
    """
    schema = load_schema()
    table_cfg = schema["tables"]["fact_content_daily_performance"]
    hf_path = table_cfg["hf_path"]
    cols = table_cfg["columns"]

    con = _hf_connection()
    where_clauses = [
        f"{cols['ga4_data_available']} = true",
        f"{cols['sessions']} > 0",
    ]
    if start_date:
        where_clauses.append(f"{cols['report_date']} >= '{start_date}'")
    if end_date:
        where_clauses.append(f"{cols['report_date']} <= '{end_date}'")
    if client_id:
        where_clauses.append(f"{cols['client_id']} = '{client_id}'")

    where_sql = " AND ".join(where_clauses)
    limit_sql = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT
            {cols['content_id']}          AS page_id,
            {cols['report_date']}         AS date,
            {cols['client_id']}           AS client_id,
            {cols['sessions']}            AS sessions,
            {cols['engaged_sessions']}    AS engaged_sessions,
            CASE 
                WHEN {cols['sessions']} > 0 
                THEN CAST({cols['engaged_sessions']} AS DOUBLE) / {cols['sessions']} 
                ELSE NULL 
            END AS engagement_rate,
            CASE 
                WHEN {cols['sessions']} > 0 
                THEN CAST({cols['total_engagement_sec']} AS DOUBLE) / {cols['sessions']} 
                ELSE NULL 
            END AS avg_engagement_time
        FROM read_parquet('{hf_path}')
        WHERE {where_sql}
        {limit_sql}
    """
    df = con.execute(query).fetchdf()
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_content_metadata(limit: int | None = None) -> pd.DataFrame:
    """Load content metadata (page-level) from dim_content."""
    schema = load_schema()
    table_cfg = schema["tables"]["dim_content"]
    hf_path = table_cfg["hf_path"]
    cols = table_cfg["columns"]

    con = _hf_connection()
    limit_sql = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT
            {cols['content_id']}           AS page_id,
            {cols['client_id']}            AS client_id,
            {cols['content_type']}         AS content_type,
            {cols['content_created_date']} AS publish_date,
            {cols['content_updated_date']} AS updated_date,
            {cols['word_count']}           AS word_count,
            {cols['search_volume']}        AS search_volume,
            {cols['competition']}          AS competition,
            {cols['cpc']}                  AS cpc,
            {cols['main_intent']}          AS main_intent,
            {cols['backlinks']}            AS backlinks,
            {cols['is_published']}         AS is_published,
            {cols['is_deleted']}           AS is_deleted
        FROM read_parquet('{hf_path}')
        WHERE {cols['is_deleted']} = false
        {limit_sql}
    """
    df = con.execute(query).fetchdf()
    if "publish_date" in df.columns:
        df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    if "updated_date" in df.columns:
        df["updated_date"] = pd.to_datetime(df["updated_date"], errors="coerce")
    return df


def load_query_90d(client_id: str | None = None, limit: int | None = None) -> pd.DataFrame:
    """Load 90-day query rollups from fact_content_query_90d."""
    schema = load_schema()
    table_cfg = schema["tables"]["fact_content_query_90d"]
    hf_path = table_cfg["hf_path"]
    cols = table_cfg["columns"]

    con = _hf_connection()
    where_sql = f"WHERE {cols['client_id']} = '{client_id}'" if client_id else ""
    limit_sql = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT
            {cols['content_id']}                    AS page_id,
            {cols['client_id']}                     AS client_id,
            {cols['query_id']}                      AS query_id,
            {cols['impressions_90d']}               AS impressions_90d,
            {cols['clicks_90d']}                    AS clicks_90d,
            {cols['avg_position_90d']}              AS avg_position_90d,
            {cols['content_total_impressions_90d']} AS content_total_impressions_90d,
            {cols['content_visible_query_count']}   AS visible_query_count,
            {cols['rare_impressions_share']}        AS rare_impressions_share
        FROM read_parquet('{hf_path}')
        {where_sql}
        {limit_sql}
    """
    return con.execute(query).fetchdf()


def load_daily_performance(
    start_date: str | None = None,
    end_date: str | None = None,
    client_id: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Load unified daily search and engagement performance in a single pass."""
    schema = load_schema()
    table_cfg = schema["tables"]["fact_content_daily_performance"]
    hf_path = table_cfg["hf_path"]
    cols = table_cfg["columns"]

    con = _hf_connection()
    where_clauses = ["1=1"]
    if start_date:
        where_clauses.append(f"{cols['report_date']} >= '{start_date}'")
    if end_date:
        where_clauses.append(f"{cols['report_date']} <= '{end_date}'")
    if client_id:
        where_clauses.append(f"{cols['client_id']} = '{client_id}'")

    where_sql = " AND ".join(where_clauses)
    limit_sql = f"LIMIT {limit}" if limit else ""

    query = f"""
        SELECT
            {cols['content_id']}          AS page_id,
            {cols['report_date']}         AS date,
            {cols['client_id']}           AS client_id,
            {cols['impressions']}         AS impressions,
            {cols['clicks']}              AS clicks,
            {cols['avg_position']}        AS avg_position,
            {cols['gsc_data_available']}  AS gsc_data_available,
            {cols['sessions']}            AS sessions,
            {cols['engaged_sessions']}    AS engaged_sessions,
            {cols['ga4_data_available']}  AS ga4_data_available,
            CASE 
                WHEN {cols['sessions']} > 0 
                THEN CAST({cols['engaged_sessions']} AS DOUBLE) / {cols['sessions']} 
                ELSE NULL 
            END AS engagement_rate,
            CASE 
                WHEN {cols['sessions']} > 0 
                THEN CAST({cols['total_engagement_sec']} AS DOUBLE) / {cols['sessions']} 
                ELSE NULL 
            END AS avg_engagement_time
        FROM read_parquet('{hf_path}')
        WHERE {where_sql}
        {limit_sql}
    """
    df = con.execute(query).fetchdf()
    df["date"] = pd.to_datetime(df["date"])
    return df
