# CTR & Engagement Opportunity Scoring for Search Content

> FlyRank ML Internship Capstone — Lane 4: CTR / Engagement Opportunity Scoring

A repeatable, leakage-safe ML scoring system that identifies pages with the highest CTR/engagement opportunity, producing an actionable review queue with scores, reason codes, and recommended actions.

## 🔗 Quick Links

- **[Live Paper →](https://your-username.github.io/Capstone-Flyrank/)** *(update after deploy)*
- [PRD](./PRD.md) | [SPECS](./SPECS.md) | [Notebooks](./work/)

## 📁 Repository Structure

```
├── PRD.md / SPECS.md / README.md     # Documentation
├── Makefile                           # Single entry points for all workflows
├── config/                            # schema.yaml + params.yaml
├── backend/
│   ├── app/                           # FastAPI application
│   │   ├── api/                       # Route handlers
│   │   ├── schemas/                   # Pydantic response models
│   │   ├── services/                  # Artifact loading layer
│   │   └── core/                      # Config, paths, env
│   ├── pipeline/                      # ML pipeline modules
│   │   ├── load.py → clean.py → windows.py → features.py → labels.py
│   │   ├── split.py → baseline.py → model.py → evaluate.py
│   │   ├── score.py → anonymize.py → run_all.py
│   ├── scripts/                       # export_static.py, scan_public.py
│   └── tests/                         # Leakage + unit tests
├── frontend/                          # React + Bootstrap paper site
│   ├── src/sections/                  # One component per paper section
│   ├── src/components/                # Shared UI components
│   └── public/data/                   # Static JSON from pipeline
├── artifacts/                         # Generated outputs (raw gitignored)
├── submission/paper_url.txt           # Deployed URL (one line)
└── work/                              # Assignment + capstone notebooks
```

## 🚀 Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Hugging Face account with access to the FlyRank gated dataset

### Install
```bash
# Copy .env.example to .env and fill in your HF_TOKEN and ANON_SALT
cp .env.example .env

# Install all dependencies
make install
```

## ⚡ Workflow

```bash
# 1. Run the full ML pipeline (requires HF_TOKEN)
make pipeline

# 2. Export artifacts to frontend static JSON + privacy scan
make export
make scan

# 3. Build the frontend for deployment
make build

# Or run everything in one command:
make all
```

### Development

```bash
# Start FastAPI backend (port 8000)
make serve

# Start React frontend dev server (port 5173, API mode)
make dev

# Run tests
make test
```

## 📊 Research Question

> Can search visibility and content-performance signals be used to identify and prioritize pages with potential CTR or engagement opportunities?

## 🔒 Privacy

- All page identifiers are anonymized (salted SHA-256 hashes)
- No URLs, domains, queries, client names, or raw data are ever published
- Automated privacy scanner runs before every export and in CI

## 📄 Acknowledgments

Built on the [FlyRank ML Internship dataset](https://flyrank.ai).
