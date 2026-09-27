import { useState } from 'react'
import { api } from './api.js'

export default function AddProduct({ onAdded }) {
  const [q, setQ] = useState('')
  const [results, setResults] = useState([])
  const [chosen, setChosen] = useState(null)
  const [options, setOptions] = useState([])
  const [option, setOption] = useState('')
  const [busy, setBusy] = useState(false)

  function doSearch(e) {
    e.preventDefault()
    setChosen(null)
    setResults([])
    setBusy(true)
    api.search(q).then(rows => {
      setResults(rows)
      setBusy(false)
    })
  }

  function pick(item) {
    setChosen(item)
    api.options(item.id).then(data => {
      const opts = data.options || []
      setOptions(opts)
      setOption(opts[0] || '')
    })
  }

  function track() {
    api.track({ store_item_id: chosen.id, name: chosen.name, option_label: option })
      .then(() => {
        setChosen(null)
        setResults([])
        setQ('')
        onAdded()
      })
  }

  return (
    <div className="add">
      <form onSubmit={doSearch}>
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Search products (try: led, mat, dumbbell)…"
        />
        <button type="submit">Search</button>
      </form>

      {busy && <p className="muted">searching… (first search can be slow while the server wakes)</p>}

      {results.length > 0 && !chosen && (
        <ul className="results">
          {results.map(r => (
            <li key={r.id} onClick={() => pick(r)}>
              {r.name} <span className="muted">· {r.category}</span>
            </li>
          ))}
        </ul>
      )}

      {chosen && (
        <div className="pick">
          <span>Track <strong>{chosen.name}</strong> —</span>
          <select value={option} onChange={e => setOption(e.target.value)}>
            {options.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
          <button onClick={track}>Track this</button>
          <button className="link" onClick={() => setChosen(null)}>cancel</button>
        </div>
      )}
    </div>
  )
}
