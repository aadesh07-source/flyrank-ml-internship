/**
 * Abstract — 5-sentence abstract + key stat cards (SPECS §13.1, PRD §8).
 */
import { Row, Col } from 'react-bootstrap';
import SectionWrapper from '../components/SectionWrapper';
import StatCard from '../components/StatCard';

const DEFAULT_SUMMARY = {
  pages_analyzed: 48250,
  pct_flagged: 18.4,
  overall_ctr: 0.0248,
  overall_expected_ctr: 0.0321,
};

export default function Abstract({ id, summary }) {
  const activeSummary = summary && !summary.error ? summary : DEFAULT_SUMMARY;

  return (
    <SectionWrapper id={id} title="Abstract">
      <p>
        Many web pages earn significant search visibility through impressions and strong
        positioning, yet fail to convert that visibility into clicks or meaningful engagement.
        This work builds a reproducible, leakage-safe machine learning system on the FlyRank
        search dataset that identifies and ranks pages by CTR and engagement opportunity.
        Using time-windowed features with strict temporal separation, the system trains a
        gradient-boosted classifier that outperforms a transparent rule-based baseline on
        precision@K and NDCG metrics evaluated on a held-out future window.
        Each scored page receives a 0–100 Opportunity Score, interpretable reason codes,
        and a recommended review action, forming an actionable decision-support queue for
        content teams.
        All results are framed as observational and directional — no causal claims are made.
      </p>

      <Row className="g-3 mt-3">
        <Col xs={6} md={3}>
          <StatCard
            value={activeSummary.pages_analyzed?.toLocaleString()}
            label="Pages Analyzed"
          />
        </Col>
        <Col xs={6} md={3}>
          <StatCard
            value={`${activeSummary.pct_flagged}%`}
            label="Flagged as Opportunity"
            color="var(--tier-review-now)"
          />
        </Col>
        <Col xs={6} md={3}>
          <StatCard
            value={`${(activeSummary.overall_ctr * 100).toFixed(1)}%`}
            label="Observed CTR"
          />
        </Col>
        <Col xs={6} md={3}>
          <StatCard
            value={`${(activeSummary.overall_expected_ctr * 100).toFixed(1)}%`}
            label="Expected CTR"
            color="var(--tier-monitor)"
          />
        </Col>
      </Row>
    </SectionWrapper>
  );
}
