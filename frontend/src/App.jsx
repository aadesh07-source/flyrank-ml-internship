import { useState, useEffect } from 'react';
import { Container, Navbar, Nav } from 'react-bootstrap';
import Hero from './sections/Hero';
import Abstract from './sections/Abstract';
import Introduction from './sections/Introduction';
import DataSection from './sections/DataSection';
import Methodology from './sections/Methodology';
import Results from './sections/Results';
import Limitations from './sections/Limitations';
import Recommendations from './sections/Recommendations';
import Reproducibility from './sections/Reproducibility';
import Acknowledgments from './sections/Acknowledgments';
import { get } from './api/dataClient';

const SECTIONS = [
  { id: 'abstract', label: 'Abstract' },
  { id: 'introduction', label: 'Introduction' },
  { id: 'data', label: 'Data' },
  { id: 'methodology', label: 'Methodology' },
  { id: 'results', label: 'Results' },
  { id: 'limitations', label: 'Limitations' },
  { id: 'recommendations', label: 'Recommendations' },
  { id: 'reproducibility', label: 'Reproducibility' },
  { id: 'acknowledgments', label: 'Acknowledgments' },
];

function App() {
  const [activeSection, setActiveSection] = useState('abstract');
  const [summary, setSummary] = useState(null);
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    // Load global data; sections render built-in defaults if data is unavailable
    get('summary').then(setSummary).catch(() => {});
    get('meta').then(setMeta).catch(() => {});

    // Intersection Observer for scrollspy
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0.1 }
    );

    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <>
      <Navbar className="paper-nav" expand="xl">
        <Container fluid style={{ maxWidth: '1240px' }}>
          <Nav className="mx-auto flex-wrap justify-content-center align-items-center">
            {SECTIONS.map(({ id, label }) => (
              <Nav.Link
                key={id}
                className={activeSection === id ? 'active' : ''}
                onClick={() => scrollTo(id)}
              >
                {label}
              </Nav.Link>
            ))}
            <div className="d-flex align-items-center ms-lg-3 gap-2 my-1">
              <a
                href="https://github.com/aadesh07-source/flyrank-ml-internship"
                target="_blank"
                rel="noopener noreferrer"
                className="nav-link external-nav-link"
                title="GitHub Repository"
              >
                <span className="badge bg-dark-subtle text-dark border">GitHub</span>
              </a>
              <a
                href="https://huggingface.co/datasets/FlyRank/internship-warehouse"
                target="_blank"
                rel="noopener noreferrer"
                className="nav-link external-nav-link"
                title="Hugging Face Dataset"
              >
                <span className="badge bg-warning-subtle text-dark border">🤗 Hugging Face</span>
              </a>
            </div>
          </Nav>
        </Container>
      </Navbar>

      <div className="paper-container">
        <Hero />
        <Abstract id="abstract" summary={summary} />
        <Introduction id="introduction" />
        <DataSection id="data" meta={meta} />
        <Methodology id="methodology" />
        <Results id="results" />
        <Limitations id="limitations" />
        <Recommendations id="recommendations" />
        <Reproducibility id="reproducibility" />
        <Acknowledgments id="acknowledgments" />
      </div>
    </>
  );
}

export default App;
