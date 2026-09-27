import { useEffect, useState } from 'react'
import { api } from './api.js'
import AddProduct from './AddProduct.jsx'
import ProductDetail from './ProductDetail.jsx'

export default function App() {
  const [products, setProducts] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)

  function loadProducts() {
    setLoading(true)
    api.products().then(rows => {
      setProducts(rows)
      setLoading(false)
    })
  }

  useEffect(loadProducts, [])

  return (
    <div className="page">
      <header>
        <h1>INE Price Tracker</h1>
        <a className="export-btn" href={api.exportUrl()}>Export CSV</a>
      </header>

      <AddProduct onAdded={loadProducts} />

      <h2>Tracked products</h2>
      {loading && <p className="muted">Loading… (the server may be waking up, give it a few seconds)</p>}
      <div className="tracked">
        {products.map(p => (
          <button
            key={p.id}
            className={'prod ' + (selected && selected.id === p.id ? 'on' : '')}
            onClick={() => setSelected(p)}
          >
            <strong>{p.name}</strong>
            <span className="muted">{p.option_label}</span>
          </button>
        ))}
      </div>

      {selected && (
        <ProductDetail
          product={selected}
          onUntracked={() => { setSelected(null); loadProducts() }}
        />
      )}
    </div>
  )
}
