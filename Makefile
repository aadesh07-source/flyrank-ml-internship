# Makefile — CTR & Engagement Opportunity Scoring (FlyRank Capstone)
# Single entry points for every stage of the pipeline + deploy workflow.

.PHONY: help install pipeline export scan build test deploy clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Setup ────────────────────────────────────────────────────────────────────

install: ## Install backend + frontend dependencies
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

# ── Backend Pipeline ─────────────────────────────────────────────────────────

pipeline: ## Run the full ML pipeline (requires HF_TOKEN)
	cd backend && python -m pipeline.run_all

test: ## Run all backend tests
	cd backend && python -m pytest tests/ -v

lint: ## Lint backend code
	cd backend && ruff check . && black --check .

# ── Export & Privacy ─────────────────────────────────────────────────────────

export: ## Export pipeline artifacts to frontend static JSON
	cd backend && python scripts/export_static.py

scan: ## Run privacy scanner on all public JSON
	cd backend && python scripts/scan_public.py

# ── Frontend ─────────────────────────────────────────────────────────────────

dev: ## Start frontend dev server (API mode)
	cd frontend && VITE_DATA_MODE=api npm run dev

build: ## Build frontend for production (static mode)
	cd frontend && VITE_DATA_MODE=static npm run build

# ── Full Workflow ────────────────────────────────────────────────────────────

all: pipeline export scan build ## Run everything: pipeline → export → scan → build

# ── Backend Server ───────────────────────────────────────────────────────────

serve: ## Start FastAPI dev server
	cd backend && uvicorn app.main:app --reload --port 8000

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean: ## Remove generated artifacts
	rm -rf artifacts/raw/*.joblib artifacts/public/*.json
	rm -rf frontend/public/data/*.json
	rm -rf frontend/dist/
