"""FastAPI application entry point for FlyRank ML Capstone."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend root is on sys.path regardless of execution CWD
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    # pyrefly: ignore [missing-import]
    from app.api import eda, health, meta, recommendations, results
except ImportError:
    from backend.app.api import eda, health, meta, recommendations, results

app = FastAPI(
    title="CTR & Engagement Opportunity Scoring API",
    version="1.0.0",
    description="Backend API for the FlyRank ML Capstone research paper.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (allow local dev & frontend clients) ─────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Root Welcome / Health Status ──────────────────────────────────────────────
@app.get("/", tags=["system"])
async def root():
    """Service status and quick links."""
    return {
        "status": "healthy",
        "service": "FlyRank ML Capstone API (Lane 4: Search CTR & Engagement Opportunity Scoring)",
        "version": "1.0.0",
        "author": "Aadesh Darole",
        "documentation": "/docs",
        "endpoints": {
            "meta": "/api/v1/meta",
            "summary": "/api/v1/summary",
            "recommendations": "/api/v1/recommendations",
            "metrics": "/api/v1/results/metrics",
            "pr_curve": "/api/v1/results/pr-curve",
            "ctr_by_position": "/api/v1/eda/ctr-by-position",
            "feature_importance": "/api/v1/results/feature-importance",
        },
    }

# ── Register core routers ─────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(meta.router, prefix="/api/v1")
app.include_router(eda.router, prefix="/api/v1/eda")
app.include_router(results.router, prefix="/api/v1/results")
app.include_router(recommendations.router, prefix="/api/v1")

# ── Direct convenience aliases (support both snake_case & kebab-case) ─────────
@app.get("/api/v1/ctr_by_position", tags=["eda"])
@app.get("/api/v1/ctr-by-position", tags=["eda"])
async def alias_ctr_by_position():
    return await eda.ctr_by_position()

@app.get("/api/v1/metrics", tags=["results"])
async def alias_metrics():
    return await results.metrics()

@app.get("/api/v1/pr_curve", tags=["results"])
@app.get("/api/v1/pr-curve", tags=["results"])
async def alias_pr_curve():
    return await results.pr_curve()

@app.get("/api/v1/feature_importance", tags=["results"])
@app.get("/api/v1/feature-importance", tags=["results"])
async def alias_feature_importance():
    return await results.feature_importance()

# ── Standalone execution entry point ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

