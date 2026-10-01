/**
 * Recommendations — Filterable, sortable ranked table (SPECS §13.1, FR-11).
 */
import { useState, useEffect, useMemo } from 'react';
import { Table, Form, Row, Col, Badge } from 'react-bootstrap';
import SectionWrapper from '../components/SectionWrapper';
import ScoreBadge from '../components/ScoreBadge';
import ReasonChip from '../components/ReasonChip';
import LoadingSpinner from '../components/LoadingSpinner';
import { get } from '../api/dataClient';

export default function Recommendations({ id }) {
  const [data, setData] = useState(null);
  const [filterAction, setFilterAction] = useState('');
  const [filterType, setFilterType] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState('opportunity_score');
  const [sortDir, setSortDir] = useState('desc');
  const [displayLimit, setDisplayLimit] = useState(25);

  useEffect(() => {
    get('recommendations')
      .then(setData)
      .catch(() => setData({ items: [], total: 0 }));
  }, []);

  const items = useMemo(() => {
    if (!data?.items) return [];
    let filtered = [...data.items];

    if (filterAction) {
      filtered = filtered.filter((i) =>
        i.reason_codes?.some((c) => c === filterAction)
      );
    }
    if (filterType) {
      filtered = filtered.filter((i) => i.content_type === filterType);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (i) =>
          i.page_id?.toLowerCase().includes(q) ||
          i.recommended_action?.toLowerCase().includes(q)
      );
    }

    filtered.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      // Field normalization
      if (sortField === 'impressions') {
        valA = a.impressions ?? a.impressions_sum ?? 0;
        valB = b.impressions ?? b.impressions_sum ?? 0;
      } else if (sortField === 'ctr') {
        valA = a.ctr ?? a.ctr_smoothed ?? 0;
        valB = b.ctr ?? b.ctr_smoothed ?? 0;
      }

      valA = valA ?? 0;
      valB = valB ?? 0;
      return sortDir === 'desc' ? valB - valA : valA - valB;
    });

    return filtered;
  }, [data, filterAction, filterType, searchQuery, sortField, sortDir]);

  // Extract unique values for filters
  const actions = useMemo(() => {
    if (!data?.items) return [];
    const codes = new Set();
    data.items.forEach((i) => i.reason_codes?.forEach((c) => codes.add(c)));
    return [...codes].sort();
  }, [data]);

  const contentTypes = useMemo(() => {
    if (!data?.items) return [];
    return [...new Set(data.items.map((i) => i.content_type).filter(Boolean))].sort();
  }, [data]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  if (!data) return <LoadingSpinner message="Loading recommendations queue..." />;

  const visibleItems = items.slice(0, displayLimit);

  return (
    <SectionWrapper id={id} title="Prioritized Review Queue & Recommendations">
      <div className="section-intro mb-4">
        <p>
          Ranked review queue of search pages prioritized by <strong>Opportunity Score (0–100)</strong>.
          Each page includes specific SERP diagnostic reason codes and tailored content optimization actions.
        </p>
      </div>

      {/* ── Tier Legend Bar ────────────────────────────────────────────── */}
      <div className="tier-legend-bar mb-4">
        <span className="legend-label me-2">Action Priority Tiers:</span>
        <Badge bg="danger" className="legend-badge me-2">80–100 : Review Now (High ROI)</Badge>
        <Badge bg="warning" text="dark" className="legend-badge me-2">60–79 : Review Soon</Badge>
        <Badge bg="success" className="legend-badge me-2">40–59 : Monitor Trend</Badge>
        <Badge bg="secondary" className="legend-badge">0–39 : Low Priority</Badge>
      </div>

      {/* ── Filter Controls Card ──────────────────────────────────────── */}
      <div className="filter-card mb-4">
        <Row className="g-3 align-items-end">
          <Col xs={12} md={4}>
            <Form.Label className="filter-label">Filter by Reason Code</Form.Label>
            <Form.Select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="filter-select"
            >
              <option value="">All Reason Codes ({actions.length})</option>
              {actions.map((a) => {
                const labelMap = {
                  DECLINING_CTR: '📉 DECLINING_CTR — CTR Dropping Over Time',
                  GOOD_POS_LOW_CTR: '🎯 GOOD_POS_LOW_CTR — Good Position, Underperforming CTR',
                  HIGH_IMPR_LOW_CTR: '👁️ HIGH_IMPR_LOW_CTR — High Impressions, Weak CTR',
                  HIGH_VIS_LOW_ENG: '⏱️ HIGH_VIS_LOW_ENG — Visible Impressions, Low Engagement',
                };
                return (
                  <option key={a} value={a}>
                    {labelMap[a] || a}
                  </option>
                );
              })}
            </Form.Select>
          </Col>
          <Col xs={12} md={3}>
            <Form.Label className="filter-label">Content Taxonomy</Form.Label>
            <Form.Select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="filter-select"
            >
              <option value="">All Content Types ({contentTypes.length})</option>
              {contentTypes.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </Form.Select>
          </Col>
          <Col xs={12} md={3}>
            <Form.Label className="filter-label">Search ID or Action</Form.Label>
            <Form.Control
              type="text"
              placeholder="e.g. P-0012 or Snippet"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="filter-input"
            />
          </Col>
          <Col xs={12} md={2}>
            <Form.Label className="filter-label">Show Rows</Form.Label>
            <Form.Select
              value={displayLimit}
              onChange={(e) => setDisplayLimit(Number(e.target.value))}
              className="filter-select"
            >
              <option value={10}>10 pages</option>
              <option value={25}>25 pages</option>
              <option value={50}>50 pages</option>
              <option value={100}>All 100 pages</option>
            </Form.Select>
          </Col>
        </Row>
        <div className="d-flex justify-content-between align-items-center mt-2 pt-2 border-top">
          <small className="text-muted">
            Displaying <strong>{visibleItems.length}</strong> of <strong>{items.length}</strong> matching candidates
            {data.total != null && items.length !== data.total && ` (filtered from ${data.total} total)`}
          </small>
          {(filterAction || filterType || searchQuery) && (
            <button
              className="btn btn-link btn-sm p-0 text-decoration-none"
              onClick={() => {
                setFilterAction('');
                setFilterType('');
                setSearchQuery('');
              }}
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* ── Ranked Table Card ─────────────────────────────────────────── */}
      <div className="content-card mb-4">
        <div className="table-responsive">
          <Table className="modern-table align-middle">
            <thead>
              <tr>
                <th style={{ width: '4%' }}>#</th>
                <th style={{ width: '13%' }}>Anonymized ID</th>
                <th
                  style={{ width: '10%', cursor: 'pointer' }}
                  onClick={() => handleSort('opportunity_score')}
                  title="Click to sort by Opportunity Score"
                >
                  Score {sortField === 'opportunity_score' ? (sortDir === 'desc' ? '▼' : '▲') : ''}
                </th>
                <th style={{ width: '11%' }}>Type</th>
                <th
                  style={{ width: '11%', cursor: 'pointer' }}
                  onClick={() => handleSort('impressions')}
                  title="Click to sort by Impressions"
                >
                  Impressions {sortField === 'impressions' ? (sortDir === 'desc' ? '▼' : '▲') : ''}
                </th>
                <th
                  style={{ width: '9%', cursor: 'pointer' }}
                  onClick={() => handleSort('ctr')}
                  title="Click to sort by CTR"
                >
                  CTR {sortField === 'ctr' ? (sortDir === 'desc' ? '▼' : '▲') : ''}
                </th>
                <th style={{ width: '9%' }}>Expected</th>
                <th
                  style={{ width: '8%', cursor: 'pointer' }}
                  onClick={() => handleSort('avg_position')}
                  title="Click to sort by Average SERP Position"
                >
                  Pos {sortField === 'avg_position' ? (sortDir === 'desc' ? '▼' : '▲') : ''}
                </th>
                <th style={{ width: '14%' }}>Diagnostic Reason</th>
                <th style={{ width: '20%' }}>Recommended Action</th>
              </tr>
            </thead>
            <tbody>
              {visibleItems.map((item, i) => {
                const impr = item.impressions ?? item.impressions_sum ?? 0;
                const ctr = item.ctr ?? item.ctr_smoothed ?? 0;
                const expCtr = item.expected_ctr ?? item.ctr_expected ?? 0;
                const pos = item.avg_position ?? item.pos_mean ?? 0;

                return (
                  <tr key={item.page_id}>
                    <td className="text-muted small">{i + 1}</td>
                    <td>
                      <code className="page-id-code">{item.page_id}</code>
                    </td>
                    <td>
                      <ScoreBadge score={item.opportunity_score} />
                    </td>
                    <td>
                      <span className="content-type-pill">{item.content_type || 'General'}</span>
                    </td>
                    <td className="font-mono text-end pe-3">
                      {impr.toLocaleString()}
                    </td>
                    <td className="font-mono text-danger">
                      {(ctr * 100).toFixed(2)}%
                    </td>
                    <td className="font-mono text-muted">
                      {(expCtr * 100).toFixed(2)}%
                    </td>
                    <td className="font-mono text-center">
                      {Number(pos).toFixed(1)}
                    </td>
                    <td>
                      {item.reason_codes?.map((c) => (
                        <ReasonChip key={c} code={c} />
                      ))}
                    </td>
                    <td>
                      <span className="action-text">{item.recommended_action}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        </div>
      </div>
    </SectionWrapper>
  );
}
