/**
 * ChartCard — Wrapper for charts with title, caption, and alt text (SPECS §13.2).
 */
export default function ChartCard({ title, caption, children }) {
  return (
    <div className="chart-card" role="figure" aria-label={title}>
      <div className="chart-title">{title}</div>
      {caption && <div className="chart-caption">{caption}</div>}
      {children}
    </div>
  );
}
