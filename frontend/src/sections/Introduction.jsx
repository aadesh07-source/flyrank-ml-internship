/**
 * Introduction — Decision supported, research question, hypotheses (SPECS §13.1, PRD §2-3).
 */
import SectionWrapper from '../components/SectionWrapper';

export default function Introduction({ id }) {
  return (
    <SectionWrapper id={id} title="Introduction">
      <h3>Problem Statement</h3>
      <p>
        A content team can only review a limited number of pages per week. The central
        decision this work supports is: <strong>"Which pages should we review first for
        title, meta description, content, or engagement improvements?"</strong> Rather than
        proving causality, the system produces a ranked review queue ordered by opportunity
        magnitude.
      </p>

      <h3>Research Question</h3>
      <p>
        <em>Can search visibility and content-performance signals be used to identify and
        prioritize pages with potential CTR or engagement opportunities?</em>
      </p>

      <h3>Hypotheses</h3>
      <ul>
        <li>
          <strong>H1:</strong> Pages whose CTR is below what their position would predict,
          in a future window, can be anticipated from past-window signals better than a
          simple rule baseline.
        </li>
        <li>
          <strong>H2:</strong> A learned score gives higher precision@K and lift than
          threshold rules on the same held-out split.
        </li>
      </ul>
    </SectionWrapper>
  );
}
