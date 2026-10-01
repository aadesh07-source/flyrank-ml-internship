/**
 * Hero — Title, author, date, and external hyperlinks (SPECS §13.1).
 */
export default function Hero() {
  return (
    <header className="hero-section">
      <div className="hero-badges mb-3">
        <span className="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 rounded-pill me-2">
          FlyRank ML Internship Capstone &middot; Lane 4
        </span>
        <span className="badge bg-success-subtle text-success border border-success-subtle px-3 py-2 rounded-pill">
          Hugging Face Gated Warehouse Verified
        </span>
      </div>

      <h1>
        CTR & Engagement Opportunity Scoring<br />
        for Search Content Using Machine Learning
      </h1>

      <p className="hero-subtitle">
        A reproducible, leakage-safe machine learning ranking system prioritizing web pages
        for meta snippet, content, and engagement optimization.
      </p>

      <div className="hero-meta mb-3">
        <strong>Aadesh Darole</strong> &middot; October 2026 &middot; Capstone Project
      </div>

      {/* ── Key Links & Repositories ───────────────────────────────────── */}
      <div className="hero-links d-flex justify-content-center flex-wrap gap-2 pt-2">
        <a
          href="https://github.com/aadesh07-source/flyrank-ml-internship"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-dark btn-sm rounded-pill px-3 py-2 d-inline-flex align-items-center shadow-sm"
        >
          <svg className="me-2" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
          </svg>
          GitHub Repository
        </a>

        <a
          href="https://huggingface.co/datasets/FlyRank/internship-warehouse"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-outline-primary btn-sm rounded-pill px-3 py-2 d-inline-flex align-items-center shadow-sm"
        >
          <span className="me-2">🤗</span>
          Hugging Face: FlyRank/internship-warehouse
        </a>

        <a
          href="https://flyrank.ai"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-outline-secondary btn-sm rounded-pill px-3 py-2 d-inline-flex align-items-center shadow-sm"
        >
          <span className="me-2">🌐</span>
          FlyRank AI
        </a>
      </div>
    </header>
  );
}
