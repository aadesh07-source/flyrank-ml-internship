# SPECS: CTR & Engagement Opportunity Scoring

Technical specification for the system described in `PRD.md`.

> **Schema note:** Table and column names below are **assumed placeholders**. Confirm them in Phase 0 against the Hugging Face release (Starter Notebook 03) and update the `config/schema.yaml` mapping. Nothing else in the code should hard-code raw column names.

---

## 1. Architecture

```
┌──────────────────────┐
│ Hugging Face (gated) │  hf:// parquet
└──────────┬───────────┘
           │ DuckDB (read token via env var)
           ▼
┌────────────────────────────────────────────────────────┐
│ Pipeline (Python)                                      │
│ load → clean → window → features → label → split →     │
│ baseline → model → evaluate → score → reason/action    │
└──────────┬─────────────────────────────────────────────┘
           │ writes artifacts (parquet/JSON, anonymized)
           ▼
┌──────────────────────┐        ┌──────────────────────────┐
│ FastAPI backend      │───────▶│ React + Bootstrap paper  │
│ (dev + local explore)│  REST  │ (Vite build)             │
└──────────┬───────────┘        └────────────┬─────────────┘
           │ export_static.py                  │ reads /data/*.json
           ▼                                   ▼
   frontend/public/data/*.json  ───────▶  GitHub Pages (static)
```

**Key decision:** GitHub Pages is static, so it cannot run FastAPI. The FastAPI app is used for development, local interactive exploration, and as the **single source of truth for JSON contracts**. `export_static.py` calls the same service layer and writes the JSON files the production React build consumes. The frontend has one data client that switches between the live API (`VITE_DATA_MODE=api`) and static JSON (`VITE_DATA_MODE=static`).

## 2. Repository Layout

```
repo/
├── PRD.md
├── SPECS.md
├── README.md
├── Makefile
├── submission/
│   └── paper_url.txt              # exactly one line: deployed URL
├── work/                          # ALL assignment notebooks + capstone.ipynb
├── config/
│   ├── schema.yaml                # raw column mapping
│   └── params.yaml                # windows, thresholds, seeds
├── backend/
│   ├── pyproject.toml / requirements.txt
│   ├── app/
│   │   ├── main.py                # FastAPI app
│   │   ├── api/                   # routers
│   │   ├── schemas/               # Pydantic models
│   │   ├── services/              # artifact loading, aggregation
│   │   └── core/config.py
│   ├── pipeline/
│   │   ├── load.py                # DuckDB over hf://
│   │   ├── clean.py
│   │   ├── windows.py
│   │   ├── features.py
│   │   ├── labels.py
│   │   ├── split.py
│   │   ├── baseline.py
│   │   ├── model.py
│   │   ├── evaluate.py
│   │   ├── score.py               # opportunity score, reason codes, actions
│   │   ├── anonymize.py
│   │   └── run_all.py
│   ├── scripts/export_static.py
│   └── tests/                     # leakage + unit tests
├── artifacts/                     # generated, gitignored raw; public JSON committed
├── frontend/
│   ├── package.json, vite.config.js
│   ├── public/data/               # static JSON from export
│   └── src/
│       ├── api/dataClient.js
│       ├── components/ (charts, tables, layout)
│       ├── sections/ (one per paper section)
│       ├── App.jsx, main.jsx
└── .github/workflows/deploy.yml
```

## 3. Data Specification

### 3.1 Access
- Dataset: FlyRank ML Internship warehouse on Hugging Face (gated; read token).
- Token from `HF_TOKEN` env var only. Never committed.
- Query engine: **DuckDB** over `hf://` paths; aggregate in SQL first, then pull page-level tables into pandas.

### 3.2 Assumed logical inputs (confirm in Phase 0)

| Logical table | Expected fields |
|---|---|
| Search performance (page × date) | `page_id`, `date`, `impressions`, `clicks`, `avg_position` |
| Engagement (page × date) | `page_id`, `date`, `sessions`, `engaged_sessions` / engagement rate, optionally avg engagement time |
| Content metadata | `page_id`, `content_type`, `publish_date` (or first-seen date) |

### 3.3 Exclusions (document in paper)
- Pages with fewer than `MIN_IMPR` impressions in the feature window (default 100).
- Pages with fewer than `MIN_DAYS` days of data (default 14).
- Brand/navigational pages if identifiable without exposing identity (optional).
- Rows with null/invalid position, or clicks > impressions.

## 4. Time Windows (leakage control)

```
|<---- Feature window (W_F) ---->|<-- gap -->|<---- Label window (W_L) ---->|
        e.g. 56 days                7 days            28 days
```

- Features use only data inside `W_F`.
- Label uses only data inside `W_L`.
- A **gap** prevents boundary leakage.
- **Rolling snapshots:** generate several (feature, label) snapshot pairs by sliding the anchor date, giving multiple rows per page across time.
- **Time-aware split:** train on earlier anchors, validate on a middle anchor, test on the **latest** anchor(s).
- **Grouped split:** within train/validation, use `GroupKFold` by `page_id` so a page never appears on both sides of a fold. Test-set pages may reappear only at later anchors; report results also on "unseen pages only" as a robustness check.

All values live in `config/params.yaml`.

## 5. Feature Specification

Computed per `(page_id, anchor_date)` using only `W_F`.

| Group | Feature | Definition |
|---|---|---|
| Visibility | `impressions_sum`, `impressions_mean_daily` | Totals / mean |
| Visibility | `log_impressions` | log1p(impressions_sum) |
| Position | `pos_mean`, `pos_median`, `pos_std`, `pos_bucket` | Impression-weighted mean position; buckets: 1-3, 4-10, 11-20, 21+ |
| CTR | `ctr_obs` | clicks / impressions |
| CTR | `ctr_smoothed` | (clicks + α·prior) / (impressions + α), Bayesian shrinkage |
| CTR | `ctr_expected` | Expected CTR from position curve (fit on **train anchors only**) |
| CTR | `ctr_gap` | `ctr_expected − ctr_smoothed` |
| CTR | `ctr_ratio` | `ctr_smoothed / ctr_expected` |
| Trend | `impr_slope`, `click_slope`, `ctr_slope`, `pos_slope` | Linear slope over `W_F` (normalized) |
| Trend | `impr_wow_change`, `ctr_wow_change` | Last 7d vs previous 7d |
| Volatility | `ctr_cv`, `impr_cv` | Coefficient of variation |
| Engagement | `sessions`, `engagement_rate`, `engagement_time_mean` | If available; `eng_missing` flag otherwise |
| Engagement | `click_to_session_ratio` | sessions / clicks (sanity/engagement proxy) |
| Content | `content_age_days` | anchor_date − publish_date (or first_seen) |
| Content | `content_type` | One-hot / target-agnostic encoding |
| Content | `days_active_in_window` | Count of days with impressions |

**Rule:** `ctr_expected` is fit only on training data and applied to val/test to avoid leakage.

## 6. Label Definition

Primary label measured in the **label window `W_L`**.

1. Compute `expected_ctr_L` = position-curve CTR for the page's label-window average position (curve fit on training data).
2. Compute `actual_ctr_L` (smoothed).
3. **Missed clicks:** `missed_clicks_L = max(0, expected_ctr_L − actual_ctr_L) × impressions_L`.
4. **Binary label** `y_opportunity = 1` if:
   - `impressions_L ≥ MIN_IMPR_L`, **and**
   - `actual_ctr_L < expected_ctr_L × (1 − δ)` (default δ = 0.25, i.e., ≥25% below expectation), **and**
   - `missed_clicks_L ≥ MIN_MISSED` (default top-quartile threshold computed on train).
5. **Regression target (secondary):** `missed_clicks_L` (log1p-transformed) for ranking by magnitude.

**Engagement extension (optional):** `y_eng_opportunity = 1` when engagement rate is in the bottom quartile for its content type while impressions are above median. Reported separately; if engagement coverage is poor, the paper states this and uses CTR-only.

**Anti-leakage rules**
- No label-window quantities appear in features.
- Position curve and thresholds are fit on train anchors only.
- Features never include `y_*` derivatives (e.g., future impressions).

## 7. Baseline (Rule-Based)

Transparent thresholds computed from **training-set quantiles**:

| Rule | Condition | Reason code |
|---|---|---|
| R1 | impressions ≥ P75 AND ctr_smoothed ≤ P25 | `HIGH_IMPR_LOW_CTR` |
| R2 | pos_mean ≤ 10 AND ctr_ratio < 0.75 | `GOOD_POS_LOW_CTR` |
| R3 | impressions ≥ P50 AND engagement_rate ≤ P25 | `HIGH_VIS_LOW_ENG` |
| R4 | ctr_slope < −threshold AND impressions stable | `DECLINING_CTR` |

Baseline score = weighted count of rules fired (tie-broken by `impressions_sum`). Baseline is evaluated with the **same** metrics and test set as the ML model.

## 8. ML Model Specification

| Item | Choice |
|---|---|
| Task | Binary classification (`y_opportunity`); secondary regression on `missed_clicks_L` for ranking |
| Candidates | Logistic Regression (interpretable benchmark), `HistGradientBoostingClassifier` / LightGBM (main) |
| Preprocessing | sklearn `Pipeline` + `ColumnTransformer`; median impute + missing flags; scaling for LR |
| Imbalance | `class_weight` / sample weights; report PR-AUC (not just ROC-AUC) |
| Tuning | Small randomized search, grouped CV on train anchors; seed fixed |
| Calibration | Isotonic / Platt on validation anchor; report reliability curve |
| Explainability | Permutation importance + partial dependence (SHAP optional) |
| Persistence | `joblib` model + `model_card.json` (params, metrics, window config) |

## 9. Evaluation Specification

Both baseline and model are scored on the identical test set.

| Metric | Why |
|---|---|
| PR-AUC, ROC-AUC | Overall discrimination under imbalance |
| Precision@K, Recall@K (K = 25, 50, 100, top 10%) | Matches the "review first" workflow |
| NDCG@K using `missed_clicks_L` as gain | Rewards ranking high-value pages first |
| Lift @ top decile | Ranking value vs random |
| Expected missed clicks captured @ K | Business-style impact (observed, not causal) |
| Calibration (Brier, reliability plot) | Trust in the score |
| Bootstrap 95% CIs (by page) | Honest uncertainty |
| Segment breakdown | By content type, position bucket, content age |

**Leakage checks (automated in `tests/`)**
1. `max(feature_date) < min(label_date)` for every snapshot.
2. No `page_id` overlap between train and validation folds (grouped CV).
3. Test anchor strictly later than train anchors.
4. No label-derived or label-window columns in the feature matrix.
5. Shuffled-label sanity test: model AUC ≈ 0.5.
6. Position curve / thresholds computed on train only (asserted via fit-state test).

## 10. Opportunity Score, Reason Codes, Actions

**Opportunity Score (0-100)**

```
score = 100 × percentile_rank( 0.7 × p_opportunity + 0.3 × norm(expected_missed_clicks) )
```

`expected_missed_clicks = p_opportunity × (ctr_gap × impressions_proxy)` using feature-window values. Percentile rank is computed within the latest scoring snapshot.

**Reason codes:** assigned from the top contributing features plus baseline rules (multiple allowed, primary first).

| Reason code | Trigger (summary) | Recommended action |
|---|---|---|
| `HIGH_IMPR_LOW_CTR` | High impressions, low smoothed CTR | Review title / meta description |
| `GOOD_POS_LOW_CTR` | Position ≤ 10, CTR ratio low | CTR optimization review (snippet, intent match) |
| `HIGH_VIS_LOW_ENG` | High visibility, low engagement | Content engagement review |
| `DECLINING_CTR` | Negative CTR trend | Review content / SERP changes |
| `MODERATE` | Score 40-60, no strong rule | Monitor |
| `LOW` | Low score | No action |

**Priority tiers:** 80-100 = Review now, 60-79 = Review soon, 40-59 = Monitor, <40 = Low priority.

**Language rule:** all outputs use *"observed / directional / decision-support"* framing; no claim that an action will increase clicks.

## 11. Anonymization & Public-Safety Spec

- `page_id` → salted SHA-256 truncated to 8-12 chars (`P-3fa9c1b2`); salt stored in env, not committed.
- Never export: URLs, domains, queries, client names, raw rows.
- Content type labels kept only if generic (e.g., "blog", "product", "landing").
- Pre-commit/CI script `scripts/scan_public.py` fails if output JSON contains `http`, `www.`, `@`, or a blocklist term.
- `.gitignore`: `.env`, `data/`, `artifacts/raw/`, `*.parquet` (except approved small public aggregates).
- Published ranked table: **top N (e.g., 100) only**, anonymized, aggregated metrics rounded.

## 12. Backend API (FastAPI)

Base path `/api/v1`. All responses JSON, Pydantic-validated. CORS enabled for the local frontend.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/meta` | Dataset release label, windows, exclusions, counts (public-safe), model version |
| GET | `/summary` | Headline stats: pages analyzed, % flagged, overall CTR vs expected |
| GET | `/eda/ctr-by-position` | Observed vs expected CTR curve data |
| GET | `/eda/distributions?metric=` | Histogram bins for impressions/CTR/position/engagement |
| GET | `/eda/trends` | Aggregated time series (daily/weekly) |
| GET | `/eda/segments?by=content_type` | Segment metrics |
| GET | `/results/metrics` | Baseline vs ML metrics, CIs |
| GET | `/results/pr-curve` | PR curve points, both systems |
| GET | `/results/precision-at-k` | P@K and NDCG@K curves |
| GET | `/results/calibration` | Reliability data |
| GET | `/results/feature-importance` | Importance values |
| GET | `/recommendations?limit=&action=&content_type=&min_score=` | Ranked, paginated pages |
| GET | `/recommendations/{anon_id}` | Single page detail (anonymized) |
| GET | `/playbook` | Action definitions and tier rules |

**Sample: `GET /api/v1/recommendations?limit=3`**

```json
{
  "total": 100,
  "items": [
    {
      "rank": 1,
      "page_id": "P-3fa9c1b2",
      "opportunity_score": 94,
      "content_type": "blog",
      "impressions": 48210,
      "ctr": 0.011,
      "expected_ctr": 0.034,
      "avg_position": 6.2,
      "reason_codes": ["HIGH_IMPR_LOW_CTR"],
      "recommended_action": "Review title/meta",
      "tier": "Review now"
    }
  ]
}
```

(Values illustrative; real values come from the FlyRank data.)

**Service layer rule:** routers call `services/` functions that read from `artifacts/public/*.json|parquet`. `export_static.py` calls the same functions and writes `frontend/public/data/<endpoint>.json`, guaranteeing parity between API and static modes.

## 13. Frontend Specification (React JS + Bootstrap)

**Tooling:** Vite + React 18, `react-bootstrap` + Bootstrap 5, `react-router-dom` (HashRouter for GitHub Pages), Chart library: **Recharts** (or Chart.js via `react-chartjs-2`), `@tanstack/react-table` for the ranked table.

**Layout:** single long-form paper page with a sticky left/top section nav (Bootstrap `Navbar` + `Nav` scrollspy). Container max-width ~900px for reading; charts may span wider.

### 13.1 Sections → Components

| Paper section | Component | Contents |
|---|---|---|
| Title + Abstract | `Hero`, `Abstract` | Title, author, date, 5-sentence abstract, key-stat cards (Bootstrap `Card`) |
| Introduction | `Introduction` | Decision supported, research question, hypotheses |
| Data | `DataSection` | Release, tables used, date windows (timeline diagram), exclusions table |
| Methodology | `Methodology` | Feature table, label definition, baseline rules, validation diagram, leakage-check checklist |
| Results | `Results` | Metrics table (baseline vs ML), PR curve, P@K / NDCG@K, calibration, feature importance, segment charts, CTR-vs-position chart |
| Limitations | `Limitations` | Bulleted honest framing, "what this does not claim" callout (`Alert`) |
| Ranked Recommendations | `Recommendations` | Filterable, sortable table (score badge, reason chips, action), tier legend, CSV-free (no raw export) |
| Reproducibility | `Reproducibility` | Links to repo, `work/` notebooks, run instructions |
| Acknowledgments | `Acknowledgments` | "Built on the FlyRank ML Internship dataset" → `https://flyrank.ai` with `target="_blank" rel="noopener noreferrer"` |

### 13.2 Shared components
`SectionWrapper`, `StatCard`, `ChartCard` (title + caption + alt text), `DataTable`, `ScoreBadge` (color by tier), `ReasonChip`, `ErrorBoundary`, `LoadingSpinner`.

### 13.3 Data client

```js
// src/api/dataClient.js
const MODE = import.meta.env.VITE_DATA_MODE; // 'api' | 'static'
const BASE = MODE === 'api' ? import.meta.env.VITE_API_URL : `${import.meta.env.BASE_URL}data`;
export const get = (name, params) => /* api: /api/v1/{name}?params ; static: {BASE}/{name}.json */;
```

Static mode applies filtering/sorting client-side on the top-N JSON.

### 13.4 UX / Design requirements
- Responsive (Bootstrap grid; charts collapse on mobile).
- Light theme with high-contrast score colors; tier colors consistent across table, badges, and charts.
- Every chart has a caption stating what to observe and a plain-language takeaway.
- Print-friendly CSS (paper may be saved as PDF).
- Vite `base` set to `/<repo-name>/` for GitHub Pages.

## 14. Deployment

| Step | Detail |
|---|---|
| 1 | `make pipeline` runs `run_all.py`, writes artifacts |
| 2 | `make export` runs `export_static.py` + `scan_public.py` |
| 3 | `make build` runs `vite build` with `VITE_DATA_MODE=static` |
| 4 | GitHub Actions (`deploy.yml`) publishes `frontend/dist` to GitHub Pages on push to `main` |
| 5 | Write final URL (one line) to `submission/paper_url.txt` |

**Pages note:** the pipeline needs the gated dataset, so it is run **locally**; CI only builds and deploys the already-exported, scanned JSON. The HF token is never placed in CI.

**`submission/paper_url.txt`** example (exactly one line, no extras):

```
https://<username>.github.io/<repo-name>/
```

## 15. Configuration (`config/params.yaml`)

```yaml
seed: 42
windows:
  feature_days: 56
  gap_days: 7
  label_days: 28
  anchor_step_days: 14
filters:
  min_impressions_feature: 100
  min_impressions_label: 100
  min_days_active: 14
label:
  ctr_shortfall_delta: 0.25
  min_missed_clicks_quantile: 0.75
ctr_smoothing_alpha: 50
split:
  cv_folds: 5
  test_anchors: 1
topk: [25, 50, 100]
publish:
  top_n_recommendations: 100
```

## 16. Testing Strategy

| Type | Coverage |
|---|---|
| Unit | Feature functions, CTR smoothing, label logic, score computation |
| Leakage | The six checks in Section 9 |
| API | Pydantic schema validation, pagination/filter behavior (FastAPI `TestClient`) |
| Privacy | `scan_public.py` on all exported JSON |
| Frontend | Component smoke tests (Vitest + React Testing Library); build succeeds in static mode |
| Reproducibility | `make pipeline` twice produces identical metrics (seeded) |

## 17. Tech Stack and Versions (pin in lockfiles)

**Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, DuckDB, pandas, numpy, scikit-learn, LightGBM (optional), scipy, joblib, huggingface_hub, PyYAML, pytest.
**Frontend:** Node 20+, React 18, Vite, Bootstrap 5, react-bootstrap, react-router-dom, Recharts, @tanstack/react-table, Vitest.
**Tooling:** Makefile, GitHub Actions, ruff/black, ESLint/Prettier.

## 18. Implementation Order (suggested)

1. Phase 0: HF access, schema audit, fill `schema.yaml`, repo skeleton.
2. `load.py` + `clean.py` + EDA notebook.
3. `windows.py` + `features.py` + `labels.py` with leakage tests.
4. `baseline.py`, `split.py`, `evaluate.py`.
5. `model.py`, calibration, explainability.
6. `score.py` + `anonymize.py` → public artifacts.
7. FastAPI routers + schemas + tests.
8. React sections with static JSON (mock first, then real).
9. `export_static.py`, `scan_public.py`, GitHub Actions deploy.
10. Write paper text, limitations, abstract; set `paper_url.txt`.

## 19. Honest-Framing Language Guide (for the paper)

| Avoid | Use instead |
|---|---|
| "Changing titles will increase clicks" | "These pages are candidates for title review (decision-support)" |
| "Google ranks pages with X higher" | "Pages with X were observed to have higher CTR in this dataset (directional)" |
| "The model proves…" | "On the held-out window, the model ranked… better than the baseline (observed)" |
| Client or domain references | Anonymized page IDs only |