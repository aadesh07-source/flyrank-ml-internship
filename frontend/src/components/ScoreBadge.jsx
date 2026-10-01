/**
 * ScoreBadge — Color-coded opportunity score badge (SPECS §13.2).
 */
export default function ScoreBadge({ score }) {
  let tierClass = 'tier-low';
  if (score >= 80) tierClass = 'tier-review-now';
  else if (score >= 60) tierClass = 'tier-review-soon';
  else if (score >= 40) tierClass = 'tier-monitor';

  return <span className={`score-badge ${tierClass}`}>{score}</span>;
}
