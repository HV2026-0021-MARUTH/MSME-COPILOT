import React, { useState, useEffect } from 'react'
import { ShoppingBag, Mic, Edit3, Keyboard, Clock, IndianRupee } from 'lucide-react'

export default function SalesHistoryView() {
  const [sales, setSales] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchSalesHistory = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/sales')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSales(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSalesHistory()
  }, [])

  const getSourceBadge = (source) => {
    const srcLower = (source || 'text').toLowerCase()
    if (srcLower === 'voice') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-blue)', fontWeight: '600' }}>
          <Mic size={12} /> VOICE
        </span>
      )
    }
    if (srcLower === 'manual') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '600' }}>
          <Keyboard size={12} /> MANUAL
        </span>
      )
    }
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', fontWeight: '600' }}>
        <Edit3 size={12} /> TEXT
      </span>
    )
  }

  const formatDate = (isoStr) => {
    if (!isoStr) return ''
    const d = new Date(isoStr)
    return d.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
  }

  return (
    <div>
      <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: '700' }}>Sales History</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Past customer sales recorded via Voice, Text, or Manual entry</p>
        </div>
        <span className="badge">{sales.length} Sales Total</span>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading sales history...</div>
      ) : error ? (
        <div style={{ color: 'var(--accent-red)', padding: '1rem' }}>Failed to load sales history: {error}</div>
      ) : sales.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
          No sales recorded yet. Use the Capture view to record a sale!
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {sales.map(sale => (
            <div key={sale.id} className="card" style={{ marginBottom: 0 }}>
              <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  {getSourceBadge(sale.source)}
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Clock size={14} /> {formatDate(sale.created_at)}
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Revenue</span>
                    <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--accent-blue)' }}>₹{sale.total_amount.toFixed(2)}</span>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Profit</span>
                    <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--accent-green)' }}>₹{sale.profit.toFixed(2)} ({sale.margin_pct}%)</span>
                  </div>
                </div>
              </div>

              {/* Sale Line Items */}
              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', display: 'block', marginBottom: '0.4rem' }}>Line Items:</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {sale.items.map(item => (
                    <div key={item.id} style={{ background: '#0f172a', border: '1px solid var(--border-color)', padding: '0.35rem 0.65rem', borderRadius: '0.375rem', fontSize: '0.82rem' }}>
                      <span style={{ fontWeight: '500' }}>{item.product_name || `Product #${item.product_id}`}</span>
                      <span style={{ color: 'var(--text-muted)', marginLeft: '0.35rem' }}>× {item.quantity}</span>
                      <span style={{ color: 'var(--accent-blue)', marginLeft: '0.5rem', fontWeight: '600' }}>₹{(item.quantity * item.unit_price).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
