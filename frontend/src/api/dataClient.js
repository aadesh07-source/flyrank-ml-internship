/**
 * dataClient.js — Unified data access layer (SPECS §13.3).
 *
 * Supports three modes (VITE_DATA_MODE):
 * 1. 'static' (default): reads the committed /data/*.json artifacts — zero failing
 *    network requests, works offline and on GitHub Pages.
 * 2. 'api': explicit live FastAPI server mode (http://localhost:8000/api/v1).
 * 3. 'auto': prefers the live API when the server responds, otherwise silently
 *    falls back to static JSON. The backend is probed at most once per page load.
 */

const MODE = import.meta.env.VITE_DATA_MODE || 'static';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const BASE_URL = import.meta.env.BASE_URL || '/';

// Cached reachability flag for 'auto' mode: a backend that is offline is only
// probed once per session, so it never produces repeated failed requests
// (and red errors) in the browser console.
let apiReachable = null;

async function checkApiReachable() {
  if (apiReachable !== null) return apiReachable;
  try {
    const response = await fetch(`${API_URL}/api/v1/health`, { method: 'GET' });
    apiReachable = response.ok;
  } catch {
    apiReachable = false;
  }
  return apiReachable;
}

/**
 * Map resource name to backend endpoint path.
 */
function resolveApiPath(name) {
  if (['metrics', 'calibration'].includes(name)) {
    return `results/${name}`;
  }
  if (name === 'pr_curve') {
    return 'results/pr-curve';
  }
  if (name === 'precision_at_k') {
    return 'results/precision-at-k';
  }
  if (name === 'feature_importance') {
    return 'results/feature-importance';
  }
  if (name === 'ctr_by_position') {
    return 'eda/ctr-by-position';
  }
  if (['distributions', 'trends', 'segments'].includes(name)) {
    return `eda/${name}`;
  }
  return name;
}

/**
 * Fetch data by endpoint name.
 * @param {string} name - Endpoint/artifact name (e.g., 'meta', 'recommendations').
 * @param {object} params - Query parameters.
 * @returns {Promise<object>} Parsed JSON response.
 */
export async function get(name, params = {}) {
  // 1. Live FastAPI Backend ('api' mode always; 'auto' only when reachable)
  if (MODE === 'api' || (MODE === 'auto' && (await checkApiReachable()))) {
    try {
      const queryString = new URLSearchParams(params).toString();
      const endpoint = resolveApiPath(name);
      const apiUrl = `${API_URL}/api/v1/${endpoint}${queryString ? `?${queryString}` : ''}`;

      const response = await fetch(apiUrl, {
        headers: { Accept: 'application/json' },
      });

      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      if (MODE === 'api') {
        throw new Error(`Live API error for ${name}: ${err.message}`);
      }
      // If MODE is 'auto', seamlessly fall through to static JSON
    }
  }

  // 2. Static JSON Fallback (for offline local or GitHub Pages hosting)
  const staticUrl = `${BASE_URL}data/${name}.json`;
  const response = await fetch(staticUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${name}: ${response.status} ${response.statusText}`);
  }

  let data = await response.json();

  // Apply client-side filtering for recommendations in static fallback
  if (name === 'recommendations' && data.items) {
    let items = [...data.items];

    if (params.action) {
      items = items.filter((item) =>
        item.reason_codes?.some((c) => c.toUpperCase() === params.action.toUpperCase())
      );
    }
    if (params.content_type) {
      items = items.filter(
        (item) => item.content_type?.toLowerCase() === params.content_type.toLowerCase()
      );
    }
    if (params.min_score) {
      items = items.filter((item) => item.opportunity_score >= Number(params.min_score));
    }
    if (params.limit) {
      items = items.slice(0, Number(params.limit));
    }

    data = { ...data, total: items.length, items };
  }

  return data;
}

export default { get };

