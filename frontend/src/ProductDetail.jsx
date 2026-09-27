import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer,
} from 'recharts'
import { api } from './api.js'

export default function ProductDetail({ product, onUntracked }) {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    api.history(product.id).then(data => {
      setRows(data)
      setLoading(false)
    })
  }

  useEffect(load, [product])

  // the chart only uses runs that actually got a price
  const chartData = rows
    .filter(r => r.price != null)
    .map(r => ({ time: new Date(r.scraped_at).toLocaleString(), price: Number(r.price) }))

  function untrack() {
    if (confirm('Stop tracking this product?')) {
      api.untrack(product.id).then(onUntracked)
    }
  }

  return (
    <div className="detail">
      <div className="detail-head">
        <h3>{product.name} — {product.option_label}</h3>
        <div className="detail-actions">
          <button className="ghost small" onClick={load}>↻ Refresh</button>
          <button className="link" onClick={untrack}>stop tracking</button>
        </div>
      </div>

      {loading ? <p className="muted">loading history…</p> : (
        <>
          <h4>Price over time</h4>
          {chartData.length === 0 ? (
            <p className="muted">
              No data yet. Hit <strong>Scrape now</strong> up top, wait ~a minute,
              then click <strong>↻ Refresh</strong>.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" hide />
                <YAxis width={60} />
                <Tooltip />
                <Line type="monotone" dataKey="price" stroke="#2b6cb0" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}

          <h4>Scrape log</h4>
          <table>
            <thead>
              <tr>
                <th>time (UTC)</th><th>outcome</th><th>price</th><th>stock</th><th>tries</th>
              </tr>
            </thead>
            <tbody>
              {rows.slice().reverse().map(r => (
                <tr key={r.id} className={r.outcome === 'failed' ? 'failed' : ''}>
                  <td>{new Date(r.scraped_at).toISOString().replace('T', ' ').slice(0, 19)}</td>
                  <td>{r.outcome}</td>
                  <td>{r.price == null ? '—' : r.price}</td>
                  <td>{r.stock == null ? '—' : r.stock}</td>
                  <td>{r.tries}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
