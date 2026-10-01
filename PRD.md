# PRD: CTR & Engagement Opportunity Scoring for Search Content

**Project type:** FlyRank ML Internship Capstone, Lane 4 (CTR / Engagement Opportunity Scoring)
**Working title:** *CTR and Engagement Opportunity Scoring for Search Content Using Machine Learning*
**Stack:** Python + FastAPI (backend / pipeline), React JS + Bootstrap (frontend / paper)
**Status:** Draft v1

---

## 1. Summary

Many pages earn search visibility (impressions, decent position) but fail to turn it into clicks or engagement. This project builds a repeatable, leakage-safe ML scoring system on the FlyRank search dataset that ranks pages by **CTR / engagement opportunity** and attaches a **reason code** and **recommended review action** to each.

The final deliverable is a **publicly deployed research paper** (a React web page) backed by a reproducible repo. A FastAPI service powers the pipeline and an interactive exploration view during development; its outputs are exported as static JSON so the paper can be hosted for free.

## 2. Research Question

> Can search visibility and content-performance signals be used to identify and prioritize pages with potential CTR or engagement opportunities?

**Hypotheses**

- H1: Pages whose CTR is below what their position would predict, in a future window, can be anticipated from past-window signals better than a simple rule baseline.
- H2: A learned score gives higher precision@K and lift than threshold rules on the same held-out split.

## 3. Problem Statement / Decision Supported

A content team can only review a limited number of pages per week. The decision: **"Which pages should we review first for title/meta, content, or engagement improvements?"** The system supports this by producing a ranked review queue, not by proving causality.

## 4. Goals and Non-Goals

### Goals
1. Analyze CTR, impressions, average position, engagement, content age, content type, and trend signals.
2. Build a transparent **rule-based baseline**.
3. Build an **ML opportunity model** with a clearly defined, future-window target and leakage-safe validation.
4. Convert model output into a **0-100 Opportunity Score**, **reason codes**, and **recommended actions**.
5. Ship a deployed research paper with all required sections plus a reproducible repo.

### Non-Goals
- Proving how Google's algorithm works.
- Claiming causal impact of any title/content change.
- Exposing client names, domains, URLs, private queries, credentials, or raw exports.
- Production-grade auth, multi-user accounts, or real-time data ingestion.

## 5. Users and Personas

| Persona | Need |
|---|---|
| **Reviewer / grader** | Open the paper URL (from `submission/paper_url.txt`), read a clean paper, verify method and honesty of claims, find the repo. |
| **Content / SEO strategist** (the paper's audience) | See a ranked, explainable action list and understand its limits. |
| **The author (you)** | Run the pipeline end to end, regenerate all charts/tables, and deploy with one command. |

## 6. Scope

### In scope
- Data access via Hugging Face (gated, read token) using DuckDB over `hf://` and sklearn modeling, as taught in Starter Notebook 03.
- Feature engineering, label definition, baseline, ML model, validation, scoring, ranking, action mapping.
- FastAPI service exposing pipeline results.
- React + Bootstrap paper site with charts and an explorable ranked table.
- Static export + GitHub Pages deployment.

### Out of scope
- Live querying of the warehouse from the public site.
- Any user-uploaded data.

## 7. Key Deliverables

| # | Deliverable | Location |
|---|---|---|
| D1 | Deployed research paper (public URL) | GitHub Pages / personal site |
| D2 | `submission/paper_url.txt`, exactly one line: the deployed URL | repo root |
| D3 | All assignment notebooks + capstone notebook | `work/` |
| D4 | Backend, frontend, pipeline code | `backend/`, `frontend/` |
| D5 | `PRD.md`, `SPECS.md`, `README.md` | repo root |

## 8. Paper Requirements (mapped to site sections)

| Section | Content requirement |
|---|---|
| Title + Abstract | 5 sentences: question → method → result |
| Introduction / Problem | The decision the work supports |
| Data | Release, tables, date windows, exclusions and why (public-safe) |
| Methodology | Assumptions, features, label definition, baseline, validation design (grouped/time-aware split, leakage checks) |
| Results | Model vs baseline on the **same split**, with charts |
| Limitations & Honest Framing | "Observed / directional / decision-support" language only |
| Ranked Recommendations | Action playbook: ranked table with score, signal, reason code, action |
| Reproducibility | Links to notebooks and repo |
| Acknowledgments & Data Credit | "Built on the FlyRank ML Internship dataset" linking to https://flyrank.ai (new tab) |

## 9. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-1 | Pipeline loads FlyRank data from Hugging Face using a read token from env var | Must |
| FR-2 | Pipeline builds a page-level feature table for a **feature window** | Must |
| FR-3 | Pipeline builds a label from a **later label window** (no overlap with features) | Must |
| FR-4 | Rule-based baseline produces a flag/score per page | Must |
| FR-5 | ML model produces a probability/score per page, trained with grouped + time-aware split | Must |
| FR-6 | Baseline and model evaluated on the identical test set | Must |
| FR-7 | Opportunity Score (0-100) with reason codes and a recommended action per page | Must |
| FR-8 | Leakage checks are documented and automated (tests) | Must |
| FR-9 | FastAPI endpoints for summary, ranked pages, metrics, charts data, methodology metadata | Must |
| FR-10 | React paper renders all required sections with charts | Must |
| FR-11 | Explorable ranked table (filter by action, content type; sort by score) | Should |
| FR-12 | Page identifiers anonymized (hashed IDs); no URLs/queries/domains shown | Must |
| FR-13 | Static export script dumps API outputs to JSON for hosting | Must |
| FR-14 | One-command build and deploy to GitHub Pages | Should |
| FR-15 | Model explainability (feature importance / SHAP-style or permutation importance) | Should |

## 10. Non-Functional Requirements

- **Privacy / public safety:** zero client identifiers, URLs, queries, tokens, or raw rows in repo or site. Only aggregated or anonymized outputs are published.
- **Reproducibility:** fixed random seeds, pinned dependencies, deterministic window definitions, a single `make` or script entry point.
- **Honesty:** every claim is phrased as *observed*, *directional*, or *decision-support*; no causal or "Google ranking proof" language.
- **Performance:** site loads under ~3 s on a normal connection (data JSON kept small, top-N pages only).
- **Accessibility:** readable contrast, alt text/captions on charts, responsive layout (Bootstrap grid).

## 11. Success Metrics

| Area | Metric | Target |
|---|---|---|
| Model quality | Precision@K (K=50/100) vs baseline | ML beats baseline on same split |
| Model quality | NDCG@K, PR-AUC (or Spearman if regression) | Reported with confidence intervals (bootstrap) |
| Lift | Share of true opportunities captured in top 10% | ≥ baseline, ideally 1.5x+ |
| Validity | Leakage checks pass | 100% |
| Delivery | All 9 paper sections present; paper_url.txt valid | Yes |
| Honesty | Limitations section covers causality, sparsity, window dependence | Yes |

Note: if the ML model does **not** beat the baseline, the paper reports that honestly. That is an acceptable, valid result.

## 12. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Label leakage (using future info as features) | Strict window separation; unit tests asserting max feature date < min label date |
| Same page in train and test (page-level leakage) | GroupKFold / grouped split by page ID; time-aware holdout |
| Position confounds CTR | Use position-adjusted expected CTR (residual), not raw CTR |
| Low-impression pages produce noisy CTR | Minimum impression threshold; Bayesian/shrinkage CTR smoothing |
| Engagement data sparse or missing | Treat as secondary signal; document coverage; fall back to CTR-only label |
| Schema unknown until data access | Phase 0: data audit and schema confirmation before finalizing features |
| GitHub Pages cannot host FastAPI | Static export of API outputs; React reads JSON |
| Accidental data exposure | Hash IDs, `.gitignore` raw data and tokens, pre-commit scan for URLs/domains |

## 13. Milestones (self-paced, ~8 weeks)

| Phase | Weeks | Output |
|---|---|---|
| 0. Setup and data audit | 1-2 | HF access, schema notes, DuckDB queries, repo skeleton |
| 1. EDA | 3 | CTR/position/engagement analysis, charts, decision on label |
| 2. Lane lock | End of wk 4 | Lane 4 confirmed, label + windows finalized |
| 3. Baseline + features | 5 | Rule baseline, feature table, leakage tests |
| 4. ML model + validation | 6 | Trained model, metrics vs baseline, explainability |
| 5. Scoring + recommendations | 7 | Opportunity score, reason codes, action playbook |
| 6. Paper + deploy | 8 | React site live, `paper_url.txt`, final README |

## 14. Definition of Done

- [ ] Paper is live at a public URL with all 9 sections.
- [ ] `submission/paper_url.txt` contains exactly one line: the deployed URL.
- [ ] `work/` contains every assignment notebook and the capstone notebook.
- [ ] Model vs baseline compared on the same grouped/time-aware split, with charts.
- [ ] Limitations use observed / directional / decision-support language.
- [ ] Acknowledgment links to https://flyrank.ai (opens in new tab).
- [ ] No client names, domains, URLs, private queries, credentials, or raw exports anywhere in the repo or site.
- [ ] Repo URL submitted on the capstone.

## 15. Open Questions (resolve in Phase 0)

1. Exact table names and columns in the warehouse release (impressions, clicks, position, sessions/engagement, content type, publish date)?
2. Available date range, and is it long enough for feature window + gap + label window + test period?
3. Is engagement (e.g., engaged sessions, bounce, time) available at page level and joinable to search data?
4. Is page content metadata (type, publish date) available, or must age be inferred from first-seen date?