/**
 * Acknowledgments — Data credit with FlyRank link (SPECS §13.1, PRD §8).
 */
import SectionWrapper from '../components/SectionWrapper';

export default function Acknowledgments({ id }) {
  return (
    <SectionWrapper id={id} title="Acknowledgments & Project References">
      <div className="content-card mb-4">
        <div className="d-flex align-items-center mb-3">
          <span className="badge bg-primary-subtle text-primary border border-primary-subtle px-3 py-2 rounded-pill me-2">Data Credit</span>
          <h4 className="mb-0">
            Built on the{' '}
            <a
              href="https://flyrank.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="fw-bold text-decoration-none"
            >
              FlyRank ML Internship dataset
            </a>
          </h4>
        </div>
        <p className="mb-3">
          This capstone research was developed as part of the{' '}
          <a
            href="https://flyrank.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="fw-semibold text-decoration-none"
          >
            FlyRank ML Internship Program (Lane 4: Search CTR &amp; Engagement Opportunity Scoring)
          </a>
          . The author thanks the FlyRank team for providing secure access to the gated 81.7M-row enterprise warehouse and mentoring throughout this research project.
        </p>
        <p className="text-secondary small mb-0">
          All analysis, modeling, and conclusions expressed in this work are the author&apos;s own.
          All client identifiers are cryptographically hashed and zero raw PII is exposed.
        </p>
      </div>

      {/* ── Summary Reference Links Card ──────────────────────────────── */}
      <div className="content-card">
        <div className="card-header-custom">
          <h4 className="card-title-custom">Project Resource Links</h4>
          <span className="card-badge-custom">Verified URLs</span>
        </div>
        <div className="row g-3">
          <div className="col-12 col-md-4">
            <div className="p-3 border rounded h-100 bg-light text-center">
              <div className="fw-bold mb-1">GitHub Repository</div>
              <p className="small text-muted mb-2">Code, tests, &amp; pipelines</p>
              <a
                href="https://github.com/aadesh07-source/flyrank-ml-internship"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline-dark btn-sm rounded-pill w-100"
              >
                GitHub Repo &rarr;
              </a>
            </div>
          </div>

          <div className="col-12 col-md-4">
            <div className="p-3 border rounded h-100 bg-light text-center">
              <div className="fw-bold mb-1">Hugging Face Dataset</div>
              <p className="small text-muted mb-2">81.7M rows warehouse</p>
              <a
                href="https://huggingface.co/datasets/FlyRank/internship-warehouse"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline-primary btn-sm rounded-pill w-100"
              >
                🤗 Dataset Hub &rarr;
              </a>
            </div>
          </div>

          <div className="col-12 col-md-4">
            <div className="p-3 border rounded h-100 bg-light text-center">
              <div className="fw-bold mb-1">FlyRank AI</div>
              <p className="small text-muted mb-2">Internship provider</p>
              <a
                href="https://flyrank.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline-secondary btn-sm rounded-pill w-100"
              >
                FlyRank.ai &rarr;
              </a>
            </div>
          </div>
        </div>

        <div className="text-center text-muted small mt-4 pt-3 border-top">
          FlyRank ML Internship Capstone &middot; Lane 4: CTR &amp; Engagement Opportunity Scoring &middot; Author: Aadesh Darole
        </div>
      </div>
    </SectionWrapper>
  );
}
