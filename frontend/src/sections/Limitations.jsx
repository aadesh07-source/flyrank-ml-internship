/**
 * Limitations — Honest framing, "what this does not claim" (SPECS §13.1, §19).
 */
import { Row, Col, Badge } from 'react-bootstrap';
import SectionWrapper from '../components/SectionWrapper';

const FRAMING_PAIRS = [
  {
    avoid: "Changing titles or descriptions will increase clicks",
    useInstead: "These pages are candidates for title review (decision-support)",
    category: "Actionability",
  },
  {
    avoid: "Google's ranking algorithm penalizes pages with X",
    useInstead: "Pages with X were observed to have lower CTR in this empirical dataset (directional)",
    category: "SERP Behavior",
  },
  {
    avoid: "The machine learning model proves our optimization hypothesis",
    useInstead: "On the held-out window, the model ranked opportunities with +40% higher precision than baseline (observed)",
    category: "Model Claims",
  },
  {
    avoid: "Real client domains or raw search queries",
    useInstead: "Fully salted, non-reversible anonymized page IDs (P-XXXX) for privacy compliance",
    category: "Privacy",
  },
];

export default function Limitations({ id }) {
  return (
    <SectionWrapper id={id} title="Limitations & Honest Framing">
      {/* ── Prominent Non-Claim Callout ───────────────────────────────── */}
      <div className="honest-callout mb-4">
        <div className="d-flex align-items-center mb-2">
          <span className="badge bg-warning text-dark me-2 px-2 py-1">Crucial Scientific Boundary</span>
          <strong className="text-dark">What this research does NOT claim:</strong>
        </div>
        <p className="mb-0 text-dark small leading-relaxed">
          This system does <strong>not</strong> prove causality, nor does it guarantee that revising meta snippets will increase clicks.
          It does <strong>not</strong> infer internal search engine ranking mechanics.
          All conclusions are strictly observational, directional, and formulated to assist content teams in prioritizing manual review queues.
        </p>
      </div>

      {/* ── Known Limitations Grid ────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">Analytical & Methodological Limitations</h3>
          <span className="card-badge-custom">Method Boundaries</span>
        </div>
        <Row className="g-3">
          <Col md={6}>
            <div className="limitation-item">
              <div className="limitation-num">01</div>
              <div className="limitation-content">
                <h6>Non-Causal Association</h6>
                <p>The model identifies associative patterns between past SERP features and future underperformance; external factor interventions cannot be guaranteed causal without randomized A/B trials.</p>
              </div>
            </div>
          </Col>
          <Col md={6}>
            <div className="limitation-item">
              <div className="limitation-num">02</div>
              <div className="limitation-content">
                <h6>Position Confounding Residuals</h6>
                <p>Although position effects are normalized using an empirical expectation curve, nonlinear rank interactions and Rich Snippet layouts still introduce residual noise.</p>
              </div>
            </div>
          </Col>
          <Col md={6}>
            <div className="limitation-item">
              <div className="limitation-num">03</div>
              <div className="limitation-content">
                <h6>Sparse Behavioral GA4 Telemetry</h6>
                <p>GA4 engagement data is available for a subset of client pages. Missing engagement flags maintain model robustness but reduce depth for uninstrumented cohorts.</p>
              </div>
            </div>
          </Col>
          <Col md={6}>
            <div className="limitation-item">
              <div className="limitation-num">04</div>
              <div className="limitation-content">
                <h6>Static Temporal Windows</h6>
                <p>The 56-day feature and 28-day label windows represent a snapshot in time. High-volatility seasonal cycles require rolling periodic retraining.</p>
              </div>
            </div>
          </Col>
        </Row>
      </div>

      {/* ── Framing Guide Comparison Box ──────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="card-header-custom">
          <h3 className="card-title-custom">Honest-Framing Language Guide</h3>
          <span className="card-badge-custom">Scientific Communication</span>
        </div>
        <div className="framing-table-wrap">
          <div className="framing-row header-row">
            <div className="col-cat">Context</div>
            <div className="col-avoid">Avoid Causal Over-claiming ✗</div>
            <div className="col-use">Scientific & Directional Phrasing ✓</div>
          </div>
          {FRAMING_PAIRS.map((item, idx) => (
            <div className="framing-row" key={idx}>
              <div className="col-cat">
                <Badge bg="light" text="dark" className="border">{item.category}</Badge>
              </div>
              <div className="col-avoid text-danger small">
                "{item.avoid}"
              </div>
              <div className="col-use text-success small fw-medium">
                "{item.useInstead}"
              </div>
            </div>
          ))}
        </div>
      </div>
    </SectionWrapper>
  );
}
