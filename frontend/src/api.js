// where the backend lives. on vercel we set VITE_API_URL, otherwise this default.
const BASE = import.meta.env.VITE_API_URL || 'https://ine-price-tracker-jqoc.onrender.com'

export const api = {
  products: () => fetch(`${BASE}/api/products`).then(r => r.json()),
  search: (q) => fetch(`${BASE}/api/search?q=${encodeURIComponent(q)}`).then(r => r.json()),
  options: (id) => fetch(`${BASE}/api/options?item_id=${id}`).then(r => r.json()),
  track: (body) => fetch(`${BASE}/api/track`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  }).then(r => r.json()),
  untrack: (id) => fetch(`${BASE}/api/untrack`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }),
  }).then(r => r.json()),
  history: (pid) => fetch(`${BASE}/api/history?product_id=${pid}`).then(r => r.json()),
  scrapeNow: () => fetch(`${BASE}/api/scrape-now`, { method: 'POST' }).then(r => r.json()),
  exportUrl: () => `${BASE}/api/export.csv`,
}
