import { fetchWithAuth } from '../lib/api';
import React, { useState, useEffect } from 'react'
import { X, TrendingUp, AlertTriangle, CheckCircle, Package, ShieldAlert, ArrowUpRight } from 'lucide-react'

export default function ProductAnalyticsModal({ productId, onClose }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!productId) return
    setLoading(true)
    fetchWithAuth(`/api/analytics/products/${productId}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setData(data)
        setError(null)
      })
      .catch(err => setError('Unable to complete this action. MARUTHI backend is unavailable.'))
      .finally(() => setLoading(false))
  }, [productId])

  if (!productId) return null

  const getRiskBadge = (status) => {
    switch (status) {
      case 'OUT_OF_STOCK':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', fontWeight: '700' }}>OUT OF STOCK</span>
      case 'LOW_STOCK':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '700' }}>LOW STOCK</span>
      case 'AT_RISK':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '700' }}>AT RISK ({data?.forecast?.days_of_stock || 0}d left)</span>
      case 'HEALTHY':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', fontWeight: '700' }}>HEALTHY</span>
      default:
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(148, 163, 184, 0.15)', color: 'var(--text-muted)', fontWeight: '700' }}>NO FORECAST</span>
    }
  }

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '1rem' }}>
      <div style={{ background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.75rem', width: '100%', maxWidth: '650px', maxHeight: '90vh', overflowY: 'auto', padding: '1.5rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)' }}>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: '600' }}>Product Analytics Card</span>
            <h2 style={{ fontSize: '1.3rem', fontWeight: '700', marginTop: '0.2rem' }}>{data?.name || 'Loading Product...'}</h2>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Category: {data?.category} {data?.brand ? `| Brand: ${data.brand}` : ''}</span>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={22} />
          </button>
        </div>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading analytics...</div>
        ) : error ? (
          <div style={{ color: 'var(--accent-red)', padding: '1rem' }}>Failed to load product analytics: {error}</div>
        ) : data ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

            {/* Financial Metrics Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.75rem' }}>
              <div style={{ background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Selling Price</span>
                <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--accent-blue)' }}>₹{data.selling_price}</span>
              </div>
              <div style={{ background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Purchase Price</span>
                <span style={{ fontSize: '1.1rem', fontWeight: '700' }}>₹{data.purchase_price}</span>
              </div>
              <div style={{ background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Margin %</span>
                <span style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--accent-green)' }}>{data.margin_pct}%</span>
              </div>
              <div style={{ background: 'var(--bg-card)', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Inventory Val.</span>
                <span style={{ fontSize: '1.1rem', fontWeight: '700' }}>₹{data.inventory_value}</span>
              </div>
            </div>

            {/* Demand Forecast & Stock Coverage Box */}
            <div style={{ background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '0.5rem', padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--accent-blue)' }}>Demand Forecast Engine</h4>
                {getRiskBadge(data.forecast.stock_status)}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block' }}>Est. Daily Demand</span>
                  <strong style={{ fontSize: '1.1rem' }}>{data.forecast.forecast_daily_demand} units/day</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block' }}>Current Stock</span>
                  <strong style={{ fontSize: '1.1rem' }}>{data.current_stock} units</strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block' }}>Days of Coverage</span>
                  <strong style={{ fontSize: '1.1rem', color: data.forecast.days_of_stock < 3 ? 'var(--accent-amber)' : 'inherit' }}>
                    {data.forecast.days_of_stock !== null ? `${data.forecast.days_of_stock} days` : 'N/A'}
                  </strong>
                </div>
              </div>

              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', background: '#0f172a', padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)' }}>
                <strong>Forecast Formula:</strong> 0.5 × recent 7d ({data.forecast.explanation.recent_7d_avg}) + 0.3 × prev 7d ({data.forecast.explanation.prev_7d_avg}) + 0.2 × 30d ({data.forecast.explanation.recent_30d_avg})
              </div>
            </div>

            {/* Planning Suggestion Box */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '0.5rem', padding: '1rem' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.3rem', color: 'var(--accent-green)' }}>
                📋 {data.forecast.planning_suggestion.title}
              </h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                {data.forecast.planning_suggestion.reason}
              </p>
              {data.forecast.planning_suggestion.recommended_purchase > 0 && (
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', padding: '0.4rem 0.8rem', borderRadius: '0.375rem', fontWeight: '700', fontSize: '0.9rem' }}>
                  <ArrowUpRight size={16} /> Recommended Reorder: {data.forecast.planning_suggestion.recommended_purchase} units
                </div>
              )}
            </div>

            {/* Historical Sales Overview */}
            <div>
              <h4 style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>Historical Sales Totals</h4>
              {data.units_sold_total === 0 ? (
                <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                  No historical sales recorded for this product yet.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '0.5rem', fontSize: '0.85rem', textAlign: 'center', background: '#0f172a', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Units Sold</span>
                    <strong>{data.units_sold_total}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Total Revenue</span>
                    <strong style={{ color: 'var(--accent-blue)' }}>₹{data.revenue_total}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Total COGS</span>
                    <strong>₹{data.cost_total}</strong>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>Total Profit</span>
                    <strong style={{ color: 'var(--accent-green)' }}>₹{data.profit_total}</strong>
                  </div>
                </div>
              )}
            </div>

          </div>
        ) : null}
      </div>
    </div>
  )
}
