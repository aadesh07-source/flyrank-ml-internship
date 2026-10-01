/**
 * DataSection — Release, tables, date windows, exclusions (SPECS §13.1, PRD §8).
 */
import { Table, Badge, Row, Col } from 'react-bootstrap';
import SectionWrapper from '../components/SectionWrapper';

const DEFAULT_META = {
  dataset_label: "FlyRank ML Internship Dataset (v1.0)",
  feature_window: "2025-02-01 to 2025-03-29 (56 days)",
  label_window: "2025-04-06 to 2025-05-04 (28 days)",
  gap_days: 7,
  pages_before_exclusion: 519606,
  pages_after_exclusion: 48250,
  model_version: "1.0.0-hgb",
};

export default function DataSection({ id, meta }) {
  const dataMeta = meta && !meta.error ? meta : DEFAULT_META;

  return (
    <SectionWrapper id={id} title="Data Provenance & Windowing">
      <div className="section-intro mb-4">
        <p>
          This research utilizes the official{' '}
          <a
            href="https://huggingface.co/datasets/FlyRank/internship-warehouse"
            target="_blank"
            rel="noopener noreferrer"
            className="fw-bold text-decoration-none"
          >
            🤗 FlyRank/internship-warehouse
          </a>{' '}
          dataset on Hugging Face — a gated enterprise warehouse containing <strong>81,769,613 rows</strong> across <strong>1.17 GB</strong> of parquet files.
          Data is queried remotely using DuckDB over the <code>hf://</code> protocol without downloading raw data locally.
        </p>
        <div className="d-flex flex-wrap gap-2 pt-1">
          <span className="badge bg-light text-dark border">Total Volume: 81,769,613 Rows</span>
          <span className="badge bg-light text-dark border">Storage: 1.17 GB Parquet</span>
          <span className="badge bg-light text-dark border">Modalities: Tabular, Text</span>
          <span className="badge bg-light text-dark border">Languages: English</span>
        </div>
      </div>

      {/* ── Table Sources Overview ────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">Warehouse Tables & Access Patterns</h3>
          <a
            href="https://huggingface.co/datasets/FlyRank/internship-warehouse"
            target="_blank"
            rel="noopener noreferrer"
            className="card-badge-custom text-decoration-none"
          >
            🤗 View on Hugging Face &rarr;
          </a>
        </div>
        <div className="table-responsive">
          <Table className="modern-table align-middle">
            <thead>
              <tr>
                <th>Physical Table</th>
                <th>Volume</th>
                <th>Granularity</th>
                <th>Key Attributes Utilized</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><code>dim_clients</code></td>
                <td><strong>104</strong> rows</td>
                <td>Client dimension</td>
                <td>Client identifier, GSC/GA4 access flags, account profile</td>
              </tr>
              <tr>
                <td><code>dim_content</code></td>
                <td><strong>519,606</strong> rows</td>
                <td>Page-level dimension</td>
                <td>Content type, age, word count, search intent, keyword search volume</td>
              </tr>
              <tr>
                <td><code>fact_content_daily_performance</code></td>
                <td><strong>78,835,655</strong> rows</td>
                <td>Daily page &times; date fact</td>
                <td>GSC impressions, clicks, position + GA4 sessions, engaged sessions, duration</td>
              </tr>
              <tr>
                <td><code>fact_content_query_90d</code></td>
                <td><strong>2,414,248</strong> rows</td>
                <td>90-day query rollup</td>
                <td>Query diversity, long-tail query volume share, visible query counts</td>
              </tr>
            </tbody>
          </Table>
        </div>
      </div>

      {/* ── Time Window Architecture Diagram ──────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">Temporal Split Architecture (Leakage Control)</h3>
          <span className="card-badge-custom">Rolling Snapshots</span>
        </div>
        <p className="text-secondary small mb-3">
          To prevent future information leakage into historical feature vectors, feature and label observation periods
          are completely decoupled by a mandatory 7-day exclusion buffer:
        </p>

        <div className="timeline-container p-3 mb-3">
          <div className="timeline-bar d-flex text-center font-mono">
            <div className="timeline-seg feat-seg flex-grow-1 p-2">
              <span className="badge bg-primary mb-1">Feature Window (W_F)</span>
              <div className="small fw-bold">56 Days</div>
              <div className="text-muted extra-small">{dataMeta.feature_window}</div>
            </div>
            <div className="timeline-seg gap-seg px-3 py-2">
              <span className="badge bg-secondary mb-1">Gap Buffer</span>
              <div className="small fw-bold">{dataMeta.gap_days} Days</div>
              <div className="text-muted extra-small">No Overlap</div>
            </div>
            <div className="timeline-seg label-seg flex-grow-1 p-2">
              <span className="badge bg-danger mb-1">Label Window (W_L)</span>
              <div className="small fw-bold">28 Days</div>
              <div className="text-muted extra-small">{dataMeta.label_window}</div>
            </div>
          </div>
        </div>

        <Row className="g-3">
          <Col md={3}>
            <div className="stat-subcard">
              <div className="subcard-label">Pages Pre-Filtering</div>
              <div className="subcard-val">{dataMeta.pages_before_exclusion?.toLocaleString()}</div>
            </div>
          </Col>
          <Col md={3}>
            <div className="stat-subcard">
              <div className="subcard-label">Cohort Evaluated</div>
              <div className="subcard-val text-primary">{dataMeta.pages_after_exclusion?.toLocaleString()}</div>
            </div>
          </Col>
          <Col md={3}>
            <div className="stat-subcard">
              <div className="subcard-label">Temporal Buffer</div>
              <div className="subcard-val">{dataMeta.gap_days} Days</div>
            </div>
          </Col>
          <Col md={3}>
            <div className="stat-subcard">
              <div className="subcard-label">Model Engine</div>
              <div className="subcard-val text-success">{dataMeta.model_version}</div>
            </div>
          </Col>
        </Row>
      </div>

      {/* ── Exclusions ────────────────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">Exclusion & Quality Filtering Criteria</h3>
          <span className="card-badge-custom">Noise Reduction</span>
        </div>
        <div className="table-responsive">
          <Table className="modern-table align-middle">
            <thead>
              <tr>
                <th style={{ width: '40%' }}>Exclusion Filter</th>
                <th style={{ width: '60%' }}>Theoretical Justification</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><code>Impressions &lt; 100</code> in W_F</td>
                <td>Removes low-sample statistical noise where empirical CTR variance dominates true signal.</td>
              </tr>
              <tr>
                <td><code>Active Observation Days &lt; 14</code></td>
                <td>Guarantees sufficient longitudinal history to calculate reliable trend and trajectory slopes.</td>
              </tr>
              <tr>
                <td><code>Clicks &gt; Impressions</code></td>
                <td>Data sanity filter to remove corrupted or anomalous tracking rows.</td>
              </tr>
              <tr>
                <td><code>Average Position ≤ 0 or Null</code></td>
                <td>Excludes unranked impressions lacking deterministic SERP visibility references.</td>
              </tr>
            </tbody>
          </Table>
        </div>
      </div>
    </SectionWrapper>
  );
}
