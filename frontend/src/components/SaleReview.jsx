import { fetchWithAuth } from '../lib/api';
import React, { useState } from 'react'
import { CheckCircle, AlertTriangle, Trash2, ArrowLeft, ShieldCheck, HelpCircle } from 'lucide-react'

export default function SaleReview({ parseData, products, onConfirmSuccess, onBack }) {
  const initialItems = parseData.items || []

  const [items, setItems] = useState(initialItems)
  const [source, setSource] = useState(parseData.mode || 'text')
  const [error, setError] = useState(null)
  const [isConfirming, setIsConfirming] = useState(false)

  const handleProductChange = (index, prodId) => {
    const updated = [...items]
    const selectedProd = products.find(p => (p.product_id || p.id) === prodId)

    if (selectedProd) {
      updated[index].matched_product_id = prodId
      updated[index].matched_product_name = selectedProd.product_name || selectedProd.name
      updated[index].selling_price = selectedProd.selling_price
      updated[index].purchase_price = selectedProd.purchase_price
      updated[index].match_status = 'MATCHED'  // User explicitly confirmed selection
      updated[index].line_total = roundVal((Number(updated[index].quantity) || 1) * selectedProd.selling_price)
    } else {
      updated[index].matched_product_id = null
      updated[index].matched_product_name = null
      updated[index].match_status = 'NEEDS_MATCH'
    }
    setItems(updated)
  }

  const handleQuantityChange = (index, qty) => {
    const updated = [...items]
    const q = Number(qty) || 1
    updated[index].quantity = q
    updated[index].line_total = roundVal(q * (updated[index].selling_price || 0))
    setItems(updated)
  }

  const removeItemRow = (index) => {
    if (items.length <= 1) return
    setItems(items.filter((_, i) => i !== index))
  }

  const roundVal = (val) => Math.round(val * 100) / 100

  // Calculate live estimates for UI
  const totalRevenue = roundVal(items.reduce((acc, item) => acc + (Number(item.quantity) * Number(item.selling_price || 0)), 0))
  const totalCost = roundVal(items.reduce((acc, item) => acc + (Number(item.quantity) * Number(item.purchase_price || 0)), 0))
  const totalProfit = roundVal(totalRevenue - totalCost)
  const marginPct = totalRevenue > 0 ? roundVal((totalProfit / totalRevenue) * 100) : 0

  // Check stock availability
  const checkStockWarning = (item) => {
    if (!item.matched_product_id) return null
    const p = products.find(prod => (prod.product_id || prod.id) === item.matched_product_id)
    if (!p) return null
    if (Number(item.quantity) > p.quantity) {
      return `Insufficient stock: Available ${p.quantity}, Requested ${item.quantity}`
    }
    return null
  }

  const hasStockError = items.some(item => checkStockWarning(item) !== null)
  const hasUnmatchedError = items.some(item => !item.matched_product_id || item.match_status === 'NEEDS_MATCH')

  const handleConfirmSale = async () => {
    setError(null)

    if (hasUnmatchedError) {
      setError('Please resolve all unmatched products before confirming.')
      return
    }

    if (hasStockError) {
      setError('Cannot proceed: One or more items have insufficient stock.')
      return
    }

    try {
      setIsConfirming(true)
      const payload = {
        shop_id: 'shop_001',
        source: source,
        items: items.map(item => ({
          product_id: item.matched_product_id,
          quantity: Number(item.quantity)
        }))
      }

      const res = await fetchWithAuth('/api/sales/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to confirm sale')
      }

      const result = await res.json()
      onConfirmSuccess(result)
    } catch (err) {
      setError('Unable to complete this action. MARUTHI backend is unavailable.')
    } finally {
      setIsConfirming(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <button
          onClick={onBack}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.9rem' }}
        >
          <ArrowLeft size={16} /> Re-enter / Back
        </button>

        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Input Source: <strong style={{ color: 'var(--accent-blue)' }}>{source}</strong>
        </span>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {/* Sale Items Table */}
      <div className="card" style={{ padding: 0, overflowX: 'auto', marginBottom: '1.5rem' }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: '600' }}>Review Sale Line Items</h3>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{items.length} items parsed</span>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
          <thead>
            <tr style={{ background: '#0f172a', color: 'var(--text-muted)', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Segment / Extracted</th>
              <th style={{ padding: '0.75rem 1rem' }}>Match Status</th>
              <th style={{ padding: '0.75rem 1rem' }}>Select Product</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Qty</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Price (₹)</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Total (₹)</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => {
              const stockErr = checkStockWarning(item)
              const isAmbiguous = item.match_status === 'AMBIGUOUS'
              return (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)', background: stockErr ? 'rgba(239, 68, 68, 0.05)' : 'transparent' }}>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: '500' }}>
                    {item.extracted_name || item.raw_segment}
                    {item.confidence !== undefined && (
                      <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        <span style={{ padding: '0.15rem 0.4rem', borderRadius: '0.25rem', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-blue)', fontWeight: '600', border: '1px solid rgba(59,130,246,0.2)' }}>
                          AI Confidence: {Math.round((item.confidence || 0) * 100)}%
                        </span>
                      </span>
                    )}
                    {item.sku && (
                       <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                          SKU: {item.sku}
                       </span>
                    )}
                  </td>

                  <td style={{ padding: '0.75rem 1rem' }}>
                    {(item.match_status === 'MATCHED' || item.match_status === 'EXACT') && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', fontWeight: '600' }}>
                        <CheckCircle size={12} /> 
                        {item.match_type === 'exact_sku' ? 'Exact SKU Match' : 
                         item.match_type === 'exact_name' ? 'Exact Name Match' : 
                         item.match_type === 'alias' ? 'Alias Match' : 'Matched'}
                      </span>
                    )}
                    {item.match_type === 'fuzzy' && (item.match_status === 'MATCHED' || item.match_status === 'EXACT') && (
                      <span style={{ display: 'block', marginTop: '0.3rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                         (Fuzzy matched)
                      </span>
                    )}
                    {isAmbiguous && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '600' }}>
                        <HelpCircle size={12} /> AMBIGUOUS — PLEASE CONFIRM
                      </span>
                    )}
                    {item.match_status === 'NEEDS_MATCH' && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', fontWeight: '600' }}>
                        <AlertTriangle size={12} /> Needs Match
                      </span>
                    )}
                  </td>

                  <td style={{ padding: '0.75rem 1rem' }}>
                    <select
                      value={item.matched_product_id || ''}
                      onChange={e => handleProductChange(idx, e.target.value)}
                      style={{ width: '100%', padding: '0.4rem', background: '#0f172a', border: `1px solid ${isAmbiguous ? 'var(--accent-amber)' : 'var(--border-color)'}`, borderRadius: '0.375rem', color: 'white', fontSize: '0.85rem' }}
                    >
                      <option value="">-- Which product did you mean? --</option>
                      {item.candidates && item.candidates.length > 0 ? (
                        item.candidates.map(cand => (
                          <option key={cand.product_id} value={cand.product_id}>
                            {cand.name} (₹{cand.selling_price})
                          </option>
                        ))
                      ) : null}
                      {products.map(p => (
                        <option key={p.product_id || p.id} value={p.product_id || p.id}>
                          {p.product_name || p.name} (₹{p.selling_price})
                        </option>
                      ))}
                    </select>

                    {stockErr && (
                      <span style={{ display: 'block', color: 'var(--accent-red)', fontSize: '0.75rem', marginTop: '0.25rem', fontWeight: '500' }}>
                        ⚠️ {stockErr}
                      </span>
                    )}
                  </td>

                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={e => handleQuantityChange(idx, e.target.value)}
                      style={{ width: '65px', padding: '0.35rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white', textAlign: 'right' }}
                    />
                  </td>

                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                    ₹{(item.selling_price || 0).toFixed(2)}
                  </td>

                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontWeight: '600', color: 'var(--accent-blue)' }}>
                    ₹{((item.quantity || 1) * (item.selling_price || 0)).toFixed(2)}
                  </td>

                  <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                    <button
                      onClick={() => removeItemRow(idx)}
                      disabled={items.length <= 1}
                      style={{ background: 'none', border: 'none', color: items.length <= 1 ? 'var(--border-color)' : 'var(--accent-red)', cursor: items.length <= 1 ? 'default' : 'pointer' }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Financial Summary & Confirm Sale Button */}
      <div className="card" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', gap: '1.5rem' }}>
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Revenue</span>
            <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-blue)' }}>₹{totalRevenue.toFixed(2)}</span>
          </div>
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Est. Profit</span>
            <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-green)' }}>₹{totalProfit.toFixed(2)}</span>
          </div>
          <div>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Margin %</span>
            <span style={{ fontSize: '1.4rem', fontWeight: '700' }}>{marginPct}%</span>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem' }}>
          <button
            onClick={handleConfirmSale}
            disabled={isConfirming || hasStockError || hasUnmatchedError}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem', background: (hasStockError || hasUnmatchedError) ? 'var(--border-color)' : 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.5rem', fontWeight: '600', fontSize: '1rem', cursor: (hasStockError || hasUnmatchedError) ? 'not-allowed' : 'pointer' }}
          >
            <ShieldCheck size={20} /> {isConfirming ? 'Processing Sale...' : 'Confirm Sale'}
          </button>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            ⚠️ Inventory decreases ONLY after clicking Confirm Sale
          </span>
        </div>
      </div>
    </div>
  )
}
