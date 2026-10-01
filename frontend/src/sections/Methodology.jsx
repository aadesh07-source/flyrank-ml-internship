/**
 * Methodology — Features, labels, baseline, validation, leakage checks (SPECS §13.1).
 */
import { Table, Badge, Row, Col } from 'react-bootstrap';
import SectionWrapper from '../components/SectionWrapper';

const LEAKAGE_CHECKS = [
  {
    num: 1,
    title: 'Temporal Separation',
    condition: 'max(W_F) < min(W_L)',
    desc: 'Feature window end precedes label window start by a mandatory 7-day buffer to eliminate temporal leakage.',
    status: 'Verified',
  },
  {
    num: 2,
    title: 'Grouped Split',
    condition: 'GroupKFold(by page_id)',
    desc: 'Zero page_id overlap between cross-validation folds. A URL snapshot never appears on both sides of a fold.',
    status: 'Verified',
  },
  {
    num: 3,
    title: 'Strict Future Holdout',
    condition: 'Anchor_test > max(Anchor_train)',
    desc: 'Test split is exclusively anchored on the latest time window, simulating real-world deployment on unseen future periods.',
    status: 'Verified',
  },
  {
    num: 4,
    title: 'Feature Purity',
    condition: 'No y_ columns in X',
    desc: 'Automated static code check confirms no label window metrics or future engagement rates leak into feature extraction.',
    status: 'Verified',
  },
  {
    num: 5,
    title: 'Label Shuffling Sanity',
    condition: 'Shuffled AUC ≈ 0.50',
    desc: 'Permutation test with randomized target labels yields ROC-AUC 0.498, confirming the absence of spurious data artifacts.',
    status: 'Verified',
  },
  {
    num: 6,
    title: 'Train-Only Position Prior',
    condition: 'PosCurve fit(Train only)',
    desc: 'The expected CTR by SERP position curve is fitted strictly on training snapshots and evaluated out-of-sample.',
    status: 'Verified',
  },
];

export default function Methodology({ id }) {
  return (
    <SectionWrapper id={id} title="Methodology">
      <div className="section-intro mb-4">
        <p>
          Our methodology enforces strict temporal causality and spatial isolation across all feature engineering,
          label construction, and evaluation splits to ensure zero data leakage.
        </p>
      </div>

      {/* ── Feature Engineering ────────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">1. Feature Engineering Matrix</h3>
          <span className="card-badge-custom">56-Day Feature Window (W_F)</span>
        </div>
        <p className="text-secondary small mb-3">
          All 17 engineered features are derived strictly within the 56-day observation window preceding the anchor date.
        </p>
        <div className="table-responsive">
          <Table className="modern-table">
            <thead>
              <tr>
                <th style={{ width: '15%' }}>Category</th>
                <th style={{ width: '40%' }}>Engineered Signals</th>
                <th style={{ width: '45%' }}>Analytical Description</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><Badge bg="primary" className="category-badge">Visibility</Badge></td>
                <td><code>impressions_sum</code>, <code>log_impressions</code></td>
                <td>Total SERP visibility and log-normalized impression scale.</td>
              </tr>
              <tr>
                <td><Badge bg="info" className="category-badge">Position</Badge></td>
                <td><code>pos_mean</code>, <code>pos_median</code>, <code>pos_std</code>, <code>pos_bucket</code></td>
                <td>Impression-weighted mean ranking position and stability buckets (1-3, 4-10, 11-20, 21+).</td>
              </tr>
              <tr>
                <td><Badge bg="success" className="category-badge">CTR Signals</Badge></td>
                <td><code>ctr_obs</code>, <code>ctr_smoothed</code>, <code>ctr_expected</code>, <code>ctr_gap</code>, <code>ctr_ratio</code></td>
                <td>Empirical CTR, Bayesian shrinkage prior (α=50), and divergence from SERP position expectation.</td>
              </tr>
              <tr>
                <td><Badge bg="warning" text="dark" className="category-badge">Trends</Badge></td>
                <td><code>impr_slope</code>, <code>ctr_slope</code>, <code>impr_wow_change</code></td>
                <td>Linear trajectory slopes and 7-day vs previous 7-day week-over-week velocity.</td>
              </tr>
              <tr>
                <td><Badge bg="secondary" className="category-badge">Volatility</Badge></td>
                <td><code>ctr_cv</code>, <code>impr_cv</code></td>
                <td>Coefficient of variation capturing day-to-day traffic stability.</td>
              </tr>
              <tr>
                <td><Badge bg="dark" className="category-badge">Engagement</Badge></td>
                <td><code>sessions</code>, <code>engagement_rate</code>, <code>eng_missing</code></td>
                <td>GA4 session volume, session engagement ratio, and indicator for analytics availability.</td>
              </tr>
              <tr>
                <td><Badge bg="light" text="dark" className="category-badge border">Content</Badge></td>
                <td><code>content_age_days</code>, <code>content_type</code>, <code>word_count</code></td>
                <td>Page age relative to anchor, publishing taxonomy, and length signal.</td>
              </tr>
            </tbody>
          </Table>
        </div>
      </div>

      {/* ── Label Formulation ──────────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">2. Ground Truth Target Formulation</h3>
          <span className="card-badge-custom">28-Day Label Window (W_L)</span>
        </div>
        <p className="text-secondary small mb-3">
          The binary opportunity label <code>y_opportunity ∈ {'{0, 1}'}</code> represents actionable future underperformance:
        </p>
        <div className="label-formula-box mb-3">
          <div className="formula-item">
            <strong>Condition A (CTR Gap):</strong> <code>CTR_actual(W_L) &lt; 0.75 × CTR_expected(Pos_W_L)</code>
          </div>
          <div className="formula-item mt-2">
            <strong>Condition B (Volume Scale):</strong> <code>Missed_Clicks(W_L) &gt; Q75(Missed_Clicks_Train)</code>
          </div>
        </div>
        <p className="text-muted small">
          A page is only flagged if it underperformed expected CTR by at least 25% <em>and</em> had sufficient search volume
          to produce material missed traffic.
        </p>
      </div>

      {/* ── Baseline Rules ────────────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">3. Rule-Based Industry Baseline</h3>
          <span className="card-badge-custom">Transparent Heuristics</span>
        </div>
        <p className="text-secondary small mb-3">
          Standard SEO practitioner heuristics benchmarked against the predictive ML model:
        </p>
        <div className="table-responsive">
          <Table className="modern-table">
            <thead>
              <tr>
                <th style={{ width: '10%' }}>Rule</th>
                <th style={{ width: '50%' }}>Empirical Condition</th>
                <th style={{ width: '25%' }}>System Reason Code</th>
                <th style={{ width: '15%' }}>Priority</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>R1</strong></td>
                <td>Impressions ≥ P75 <code>AND</code> CTR ≤ P25</td>
                <td><Badge bg="danger" className="reason-code-badge">HIGH_IMPR_LOW_CTR</Badge></td>
                <td>High</td>
              </tr>
              <tr>
                <td><strong>R2</strong></td>
                <td>Average Position ≤ 10 <code>AND</code> CTR Ratio &lt; 0.75</td>
                <td><Badge bg="danger" className="reason-code-badge">GOOD_POS_LOW_CTR</Badge></td>
                <td>High</td>
              </tr>
              <tr>
                <td><strong>R3</strong></td>
                <td>Impressions ≥ P50 <code>AND</code> Engagement Rate ≤ P25</td>
                <td><Badge bg="warning" text="dark" className="reason-code-badge">HIGH_VIS_LOW_ENG</Badge></td>
                <td>Medium</td>
              </tr>
              <tr>
                <td><strong>R4</strong></td>
                <td>CTR Slope declining (slope &lt; -0.05) with stable impressions</td>
                <td><Badge bg="info" className="reason-code-badge">DECLINING_CTR</Badge></td>
                <td>Medium</td>
              </tr>
            </tbody>
          </Table>
        </div>
      </div>

      {/* ── Leakage Checks Grid ────────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">4. Six-Point Leakage Prevention Audit</h3>
          <Badge bg="success" className="px-3 py-2">All 6 Passed ✓</Badge>
        </div>
        <p className="text-secondary small mb-3">
          To guarantee rigorous scientific validity, our automated test suite executes six continuous verification checks:
        </p>
        <Row className="g-3">
          {LEAKAGE_CHECKS.map((chk) => (
            <Col md={6} key={chk.num}>
              <div className="leakage-card">
                <div className="leakage-header">
                  <span className="check-number">{chk.num}</span>
                  <div className="leakage-title-wrap">
                    <h5 className="leakage-title">{chk.title}</h5>
                    <code className="leakage-cond">{chk.condition}</code>
                  </div>
                  <Badge bg="success" className="check-badge">✓ {chk.status}</Badge>
                </div>
                <p className="leakage-desc">{chk.desc}</p>
              </div>
            </Col>
          ))}
        </Row>
      </div>
    </SectionWrapper>
  );
}
