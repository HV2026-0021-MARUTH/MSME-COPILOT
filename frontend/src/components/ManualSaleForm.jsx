import { fetchWithAuth } from '../lib/api';
import React, { useState } from 'react'
import { Plus, Trash2, ShieldCheck, ArrowLeft } from 'lucide-react'

export default function ManualSaleForm({ products, onConfirmSuccess, onBack }) {
  const [items, setItems] = useState([
    { product_id: products[0]?.product_id || products[0]?.id || '', quantity: 1 }
  ])
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleItemChange = (index, field, value) => {
    const updated = [...items]
    updated[index][field] = value
    setItems(updated)
  }

  const addItemRow = () => {
    setItems([
      ...items,
      { product_id: products[0]?.product_id || products[0]?.id || '', quantity: 1 }
    ])
  }

  const removeItemRow = (index) => {
    if (items.length <= 1) return
    setItems(items.filter((_, i) => i !== index))
  }

  // Calculate live preview metrics from selected DB products
  let totalRevenue = 0.0
  let totalCost = 0.0

  items.forEach(item => {
    const p = products.find(prod => (prod.product_id || prod.id) === item.product_id)
    if (p) {
      const qty = Number(item.quantity) || 0
      totalRevenue += qty * (p.selling_price || 0)
      totalCost += qty * (p.purchase_price || 0)
    }
  })

  totalRevenue = Math.round(totalRevenue * 100) / 100
  totalCost = Math.round(totalCost * 100) / 100
  const totalProfit = Math.round((totalRevenue - totalCost) * 100) / 100
  const marginPct = totalRevenue > 0 ? Math.round((totalProfit / totalRevenue) * 10000) / 100 : 0

  const checkStockWarning = (item) => {
    const p = products.find(prod => (prod.product_id || prod.id) === item.product_id)
    if (!p) return null
    if (Number(item.quantity) > p.quantity) {
      return `Insufficient stock: Available ${p.quantity}, Requested ${item.quantity}`
    }
    return null
  }

  const hasStockError = items.some(i => checkStockWarning(i) !== null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (items.length === 0) {
      setError('Please add at least one line item.')
      return
    }

    if (hasStockError) {
      setError('Cannot proceed: One or more products have insufficient stock.')
      return
    }

    try {
      setIsSubmitting(true)
      const payload = {
        shop_id: 'shop_001',
        source: 'manual',
        items: items.map(i => ({
          product_id: i.product_id,
          quantity: Number(i.quantity)
        }))
      }

      const res = await fetchWithAuth('/api/sales/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Manual sale confirmation failed')
      }

      const result = await res.json()
      onConfirmSuccess(result)
    } catch (err) {
      setError('Unable to complete this action. MARUTHI backend is unavailable.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '1rem' }}>
        <button
          onClick={onBack}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem' }}
        >
          <ArrowLeft size={16} /> Back to Sales Capture
        </button>
      </div>

      <div className="card">
        <h3 style={{ fontSize: '1.2rem', fontWeight: '600', marginBottom: '1rem' }}>🧾 Enter Sale Manually</h3>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: '500', color: 'var(--text-main)' }}>Select Sale Products</label>
              <button
                type="button"
                onClick={addItemRow}
                style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer', fontSize: '0.85rem' }}
              >
                <Plus size={14} /> Add Line Item
              </button>
            </div>

            {items.map((item, idx) => {
              const selectedProd = products.find(p => (p.product_id || p.id) === item.product_id)
              const stockErr = checkStockWarning(item)
              return (
                <div key={idx} style={{ background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.5rem', padding: '0.75rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 40px', gap: '0.5rem', alignItems: 'center' }}>
                    <select
                      value={item.product_id}
                      onChange={e => handleItemChange(idx, 'product_id', e.target.value)}
                      style={{ padding: '0.5rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                    >
                      {products.map(p => (
                        <option key={p.product_id || p.id} value={p.product_id || p.id}>
                          {p.product_name || p.name} (₹{p.selling_price})
                        </option>
                      ))}
                    </select>

                    <input
                      type="number"
                      min="1"
                      placeholder="Qty"
                      value={item.quantity}
                      onChange={e => handleItemChange(idx, 'quantity', e.target.value)}
                      style={{ padding: '0.5rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white', textAlign: 'right' }}
                    />

                    <div style={{ textAlign: 'right', fontWeight: '600', color: 'var(--accent-blue)', fontSize: '0.95rem' }}>
                      ₹{((Number(item.quantity) || 0) * (selectedProd?.selling_price || 0)).toFixed(2)}
                    </div>

                    <button
                      type="button"
                      onClick={() => removeItemRow(idx)}
                      disabled={items.length <= 1}
                      style={{ background: 'none', border: 'none', color: items.length <= 1 ? 'var(--border-color)' : 'var(--accent-red)', cursor: items.length <= 1 ? 'default' : 'pointer' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  {stockErr && (
                    <span style={{ display: 'block', color: 'var(--accent-red)', fontSize: '0.75rem', marginTop: '0.4rem', fontWeight: '500' }}>
                      ⚠️ {stockErr}
                    </span>
                  )}
                </div>
              )
            })}
          </div>

          {/* Live Financial Calculation Preview */}
          <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Revenue</span>
              <span style={{ fontSize: '1.3rem', fontWeight: '700', color: 'var(--accent-blue)' }}>₹{totalRevenue.toFixed(2)}</span>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Est. Cost (COGS)</span>
              <span style={{ fontSize: '1.3rem', fontWeight: '700' }}>₹{totalCost.toFixed(2)}</span>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Est. Profit</span>
              <span style={{ fontSize: '1.3rem', fontWeight: '700', color: 'var(--accent-green)' }}>₹{totalProfit.toFixed(2)}</span>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Margin %</span>
              <span style={{ fontSize: '1.3rem', fontWeight: '700' }}>{marginPct}%</span>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              onClick={onBack}
              style={{ padding: '0.5rem 1rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-muted)', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || hasStockError}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.6rem 1.25rem', background: hasStockError ? 'var(--border-color)' : 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.375rem', cursor: hasStockError ? 'not-allowed' : 'pointer', fontWeight: '600' }}
            >
              <ShieldCheck size={18} /> {isSubmitting ? 'Confirming...' : 'Confirm Sale'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
