/**
 * StatCard — Headline stat card with value + label (SPECS §13.2).
 */
export default function StatCard({ value, label, color }) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={color ? { color } : {}}>
        {value ?? '—'}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  );
}
