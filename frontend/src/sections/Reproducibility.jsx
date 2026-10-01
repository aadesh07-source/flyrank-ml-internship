/**
 * Reproducibility — Links to repo, notebooks, run instructions (SPECS §13.1).
 */
import SectionWrapper from '../components/SectionWrapper';
import { Row, Col } from 'react-bootstrap';

export default function Reproducibility({ id }) {
  return (
    <SectionWrapper id={id} title="Reproducibility & Open Artifacts">
      <div className="section-intro mb-4">
        <p>
          All model code, feature engineering logic, evaluation pipelines, and research documentation are open-sourced
          under MIT License for full verification and auditability.
        </p>
      </div>

      {/* ── Key Repositories Card ─────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">Primary Project Hyperlinks</h3>
          <span className="card-badge-custom">Open Access</span>
        </div>
        <Row className="g-3">
          <Col md={6}>
            <div className="p-3 border rounded bg-light">
              <div className="fw-bold mb-1">
                <svg className="me-2" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
                </svg>
                GitHub Project Repository
              </div>
              <p className="text-secondary small mb-2">Contains complete backend pipeline, tests, API server, and React paper app.</p>
              <a
                href="https://github.com/aadesh07-source/flyrank-ml-internship"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline-dark btn-sm font-mono text-break"
              >
                github.com/aadesh07-source/flyrank-ml-internship
              </a>
            </div>
          </Col>

          <Col md={6}>
            <div className="p-3 border rounded bg-light">
              <div className="fw-bold mb-1">
                <span className="me-2">🤗</span>
                Hugging Face Dataset
              </div>
              <p className="text-secondary small mb-2">Gated warehouse containing 81.7M rows across dim_content, daily performance, and queries.</p>
              <a
                href="https://huggingface.co/datasets/FlyRank/internship-warehouse"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-outline-primary btn-sm font-mono text-break"
              >
                huggingface.co/datasets/FlyRank/internship-warehouse
              </a>
            </div>
          </Col>
        </Row>
      </div>

      {/* ── Notebooks & Config ────────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">Notebooks &amp; Core Configuration</h3>
          <span className="card-badge-custom">Declarative YAML</span>
        </div>
        <Row className="g-3">
          <Col md={6}>
            <div className="p-3 border rounded">
              <div className="fw-bold mb-1">📓 Research Notebooks (work/)</div>
              <p className="text-secondary small mb-0">
                Weekly exploration notebooks along with the standalone <code>work/capstone.ipynb</code> demonstrate remote DuckDB queries, exploratory data analysis, and model calibration curves.
              </p>
            </div>
          </Col>
          <Col md={6}>
            <div className="p-3 border rounded">
              <div className="fw-bold mb-1">⚙️ Parameter &amp; Schema Configs</div>
              <p className="text-secondary small mb-0">
                <code>config/params.yaml</code> defines all tuneable parameters (56d feature, 7d gap, 28d label). <code>config/schema.yaml</code> maps raw column names.
              </p>
            </div>
          </Col>
        </Row>
      </div>
    </SectionWrapper>
  );
}
