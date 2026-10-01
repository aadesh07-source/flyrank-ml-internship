"""explore_dataset.py — Phase 0 dataset exploration via DuckDB over hf://

This script:
1. Connects to FlyRank/internship-warehouse on Hugging Face
2. Verifies authentication
3. Lists available tables (parquet files)
4. Inspects schemas of key tables
5. Runs small sample queries
6. Shows relevant columns for CTR / engagement analysis

Usage:
    python explore_dataset.py
"""

import os
import sys

# Load .env file manually (no external dependency needed)
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("ERROR: HF_TOKEN not found. Set it in .env or as an environment variable.")
    sys.exit(1)

print(f"✓ HF_TOKEN loaded (starts with {HF_TOKEN[:6]}...)")

import duckdb

DATASET = "FlyRank/internship-warehouse"
HF_BASE = f"hf://datasets/{DATASET}"

# ── Step 1: Connect and authenticate ─────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 1: Connect to Hugging Face dataset")
print("=" * 70)

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"""
    CREATE SECRET hf_secret (
        TYPE HUGGINGFACE,
        TOKEN '{HF_TOKEN}'
    );
""")
print(f"✓ DuckDB connected with HF authentication")
print(f"  Dataset: {DATASET}")

# ── Step 2: List available tables ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 2: List available tables (parquet files)")
print("=" * 70)

# Try common patterns to discover tables
table_patterns = [
    "dim_content",
    "fact_content_daily_performance", 
    "fact_content_query_90d",
    # Also try without prefixes
    "content",
    "performance",
    "queries",
]

discovered_tables = []

# First, try to list the directory structure
try:
    result = con.execute(f"""
        SELECT file_name 
        FROM glob('{HF_BASE}/**/*.parquet')
        LIMIT 50
    """).fetchall()
    print("\nParquet files found via glob:")
    for row in result:
        print(f"  📁 {row[0]}")
except Exception as e:
    print(f"  glob approach failed: {e}")
    print("  Trying direct table access...")

# Try each table pattern directly
for table_name in table_patterns:
    patterns_to_try = [
        f"{HF_BASE}/{table_name}/*.parquet",
        f"{HF_BASE}/{table_name}/**/*.parquet",
        f"{HF_BASE}/data/{table_name}/*.parquet",
        f"{HF_BASE}/{table_name}.parquet",
    ]
    for pattern in patterns_to_try:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pattern}')").fetchone()[0]
            print(f"\n  ✓ {table_name}: {count:,} rows")
            print(f"    Pattern: {pattern}")
            discovered_tables.append((table_name, pattern))
            break
        except Exception:
            continue

if not discovered_tables:
    # Fallback: try reading the dataset root
    print("\n  Trying root-level parquet access...")
    try:
        result = con.execute(f"""
            SELECT * FROM read_parquet('{HF_BASE}/**/*.parquet') LIMIT 1
        """)
        cols = [desc[0] for desc in result.description]
        count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{HF_BASE}/**/*.parquet')").fetchone()[0]
        print(f"  ✓ Root dataset: {count:,} rows, {len(cols)} columns")
        print(f"    Columns: {cols}")
        discovered_tables.append(("root", f"{HF_BASE}/**/*.parquet"))
    except Exception as e:
        print(f"  Root access also failed: {e}")

    # Try the HF datasets approach with config/split
    print("\n  Trying HF datasets config/split patterns...")
    for split in ["train", "test", "default"]:
        try:
            pattern = f"{HF_BASE}/{split}/*.parquet"
            count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pattern}')").fetchone()[0]
            print(f"  ✓ Split '{split}': {count:,} rows")
            discovered_tables.append((split, pattern))
        except Exception:
            pass

    for config in ["dim_content", "fact_content_daily_performance", "fact_content_query_90d", "default"]:
        for split in ["train", "default"]:
            try:
                pattern = f"{HF_BASE}/{config}/{split}/*.parquet"
                count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pattern}')").fetchone()[0]
                print(f"  ✓ Config '{config}' / Split '{split}': {count:,} rows")
                discovered_tables.append((f"{config}/{split}", pattern))
            except Exception:
                pass

print(f"\n  Total tables discovered: {len(discovered_tables)}")

# ── Step 3: Inspect schemas ───────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 3: Inspect table schemas")
print("=" * 70)

for table_name, pattern in discovered_tables:
    print(f"\n  📋 Schema for: {table_name}")
    print(f"  {'─' * 50}")
    try:
        result = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{pattern}')")
        schema = result.fetchall()
        for col_name, col_type, *rest in schema:
            print(f"    {col_name:40s}  {col_type}")
    except Exception as e:
        print(f"    Error: {e}")

# ── Step 4: Sample data ──────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 4: Sample data from each table")
print("=" * 70)

for table_name, pattern in discovered_tables:
    print(f"\n  📊 Sample from: {table_name} (5 rows)")
    print(f"  {'─' * 50}")
    try:
        result = con.execute(f"SELECT * FROM read_parquet('{pattern}') LIMIT 5")
        cols = [desc[0] for desc in result.description]
        rows = result.fetchall()
        
        # Print header
        header = " | ".join(f"{c[:20]:20s}" for c in cols[:8])
        print(f"    {header}")
        print(f"    {'─' * len(header)}")
        
        # Print rows
        for row in rows:
            row_str = " | ".join(f"{str(v)[:20]:20s}" for v in row[:8])
            print(f"    {row_str}")
        
        if len(cols) > 8:
            print(f"    ... and {len(cols) - 8} more columns")
    except Exception as e:
        print(f"    Error: {e}")

# ── Step 5: CTR-relevant columns analysis ─────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 5: CTR / Engagement relevant columns")
print("=" * 70)

ctr_keywords = ["click", "ctr", "impression", "position", "session", "engage", 
                 "bounce", "time", "page", "url", "content", "type", "date", "view"]

for table_name, pattern in discovered_tables:
    try:
        result = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{pattern}')")
        schema = result.fetchall()
        relevant = []
        for col_name, col_type, *rest in schema:
            if any(kw in col_name.lower() for kw in ctr_keywords):
                relevant.append((col_name, col_type))
        
        if relevant:
            print(f"\n  🎯 Relevant columns in {table_name}:")
            for col_name, col_type in relevant:
                print(f"    ✓ {col_name:40s}  {col_type}")
    except Exception as e:
        print(f"    Error scanning {table_name}: {e}")

# ── Step 6: Quick stats ──────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 6: Quick stats (date ranges, row counts)")
print("=" * 70)

for table_name, pattern in discovered_tables:
    try:
        result = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{pattern}')")
        schema = result.fetchall()
        col_names = [s[0] for s in schema]
        
        # Find date columns
        date_cols = [c for c in col_names if "date" in c.lower() or "day" in c.lower() or "time" in c.lower()]
        
        count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pattern}')").fetchone()[0]
        print(f"\n  📈 {table_name}: {count:,} total rows")
        
        for dc in date_cols[:2]:
            try:
                min_d, max_d = con.execute(f"""
                    SELECT MIN("{dc}"), MAX("{dc}") 
                    FROM read_parquet('{pattern}')
                """).fetchone()
                print(f"    {dc}: {min_d} → {max_d}")
            except Exception:
                pass
                
    except Exception as e:
        print(f"    Error: {e}")

print("\n" + "=" * 70)
print("EXPLORATION COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("  1. Update config/schema.yaml with actual column names")
print("  2. Update config/params.yaml with actual date ranges")
print("  3. Run the pipeline: make pipeline")

con.close()
