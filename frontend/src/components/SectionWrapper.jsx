/**
 * SectionWrapper — Wraps each paper section with consistent spacing and ID (SPECS §13.2).
 */
export default function SectionWrapper({ id, title, children }) {
  return (
    <section id={id} className="paper-section">
      {title && <h2>{title}</h2>}
      {children}
    </section>
  );
}
