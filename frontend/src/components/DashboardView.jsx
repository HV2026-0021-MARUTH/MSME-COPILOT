import { fetchWithAuth } from '../lib/api';
import React, { useState, useEffect } from 'react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { TrendingUp, AlertTriangle, Package, ShieldCheck, ArrowUpRight, Clock, HelpCircle, Eye } from 'lucide-react'
import ProductAnalyticsModal from './ProductAnalyticsModal'

export default function DashboardView() {
  const [dashboardData, setDashboardData] = useState(null)
  const [trendDays, setTrendDays] = useState(30)
  const [trendData, setTrendData] = useState([])
  const [productsPerf, setProductsPerf] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [selectedProductId, setSelectedProductId] = useState(null)

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const [dashRes, trendRes, prodRes] = await Promise.all([
        fetchWithAuth('/api/dashboard'),
        fetchWithAuth(`/api/analytics/sales-trend?days=${trendDays}`),
        fetchWithAuth('/api/analytics/products')
      ])

      if (!dashRes.ok || !trendRes.ok || !prodRes.ok) {
        throw new Error('Failed to fetch dashboard analytics')
      }

      const dashJson = await dashRes.json()
      const trendJson = await trendRes.json()
      const prodJson = await prodRes.json()

      setDashboardData(dashJson)
      setTrendData(trendJson.data || [])
      setProductsPerf(prodJson || [])
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [trendDays])

  const getRiskBadge = (status) => {
    switch (status) {
      case 'OUT_OF_STOCK':
        return <span style={{ padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', fontWeight: '700' }}>OUT OF STOCK</span>
      case 'LOW_STOCK':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '700' }}>LOW STOCK</span>
      case 'AT_RISK':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '700' }}>AT RISK</span>
      case 'HEALTHY':
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', fontWeight: '700' }}>HEALTHY</span>
      default:
        return <span style={{ padding: '0.2rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(148, 163, 184, 0.15)', color: 'var(--text-muted)', fontWeight: '700' }}>NO FORECAST</span>
    }
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Loading Real Database Analytics...</div>
  }

  if (error) {
    return <div style={{ color: 'var(--accent-red)', padding: '1rem' }}>Failed to load dashboard: {error}</div>
  }

  return (
    <div>
      {/* 1. Top KPI Summary Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Today Revenue</span>
          <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-blue)' }}>₹{dashboardData.today_revenue}</span>
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Today Profit</span>
          <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-green)' }}>₹{dashboardData.today_profit}</span>
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Today Margin</span>
          <span style={{ fontSize: '1.4rem', fontWeight: '700' }}>{dashboardData.today_margin}%</span>
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Inventory Value</span>
          <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-green)' }}>₹{dashboardData.inventory_value}</span>
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Low Stock Items</span>
          <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-amber)' }}>{dashboardData.low_stock_count}</span>
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block' }}>Out of Stock</span>
          <span style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-red)' }}>{dashboardData.out_of_stock_count}</span>
        </div>
      </div>

      {/* 2. Sales Trend Recharts Chart */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '600' }}>Sales & Profit Trend</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Daily historical aggregated revenue and profit</span>
          </div>

          <div style={{ display: 'flex', gap: '0.4rem' }}>
            {[7, 30, 90].map(d => (
              <button
                key={d}
                onClick={() => setTrendDays(d)}
                style={{ padding: '0.35rem 0.75rem', borderRadius: '0.375rem', background: trendDays === d ? 'var(--accent-blue)' : 'var(--bg-card)', color: trendDays === d ? 'white' : 'var(--text-muted)', border: '1px solid var(--border-color)', fontSize: '0.8rem', fontWeight: '600', cursor: 'pointer' }}
              >
                {d} Days
              </button>
            ))}
          </div>
        </div>

        <div style={{ width: '100%', height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorProf" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: 'white' }} />
              <Area type="monotone" dataKey="revenue" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRev)" name="Revenue (₹)" />
              <Area type="monotone" dataKey="profit" stroke="#10b981" fillOpacity={1} fill="url(#colorProf)" name="Profit (₹)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Top Sellers & Profit Leaders Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        
        {/* Top Selling Products */}
        <div className="card" style={{ marginBottom: 0 }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '600', marginBottom: '0.75rem' }}>🏆 Top Selling Products</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {dashboardData.top_selling_products.map((item, idx) => (
              <div
                key={item.product_id}
                onClick={() => setSelectedProductId(item.product_id)}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0f172a', padding: '0.6rem 0.75rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', cursor: 'pointer' }}
              >
                <div>
                  <span style={{ fontWeight: '600', fontSize: '0.88rem', display: 'block' }}>{idx + 1}. {item.name}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Category: {item.category}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontWeight: '700', color: 'var(--accent-blue)', fontSize: '0.9rem', display: 'block' }}>{item.units_sold} sold</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)' }}>₹{item.profit} profit</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Profit Leaders */}
        <div className="card" style={{ marginBottom: 0 }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: '600', marginBottom: '0.75rem' }}>💎 Profit Leaders</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {dashboardData.profit_leaders.map((item, idx) => (
              <div
                key={item.product_id}
                onClick={() => setSelectedProductId(item.product_id)}
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0f172a', padding: '0.6rem 0.75rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', cursor: 'pointer' }}
              >
                <div>
                  <span style={{ fontWeight: '600', fontSize: '0.88rem', display: 'block' }}>{idx + 1}. {item.name}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Revenue: ₹{item.revenue}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontWeight: '700', color: 'var(--accent-green)', fontSize: '0.95rem', display: 'block' }}>₹{item.profit} profit</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.units_sold} units</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* 4. Reorder Planning Suggestions Table */}
      <div className="card" style={{ padding: 0, overflowX: 'auto', marginBottom: '1.5rem' }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: '600' }}>📋 Reorder Planning Suggestions</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Deterministic baseline stock coverage & purchase recommendations</span>
          </div>
          <span className="badge">{dashboardData.reorder_suggestions.length} items flagged</span>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
          <thead>
            <tr style={{ background: '#0f172a', color: 'var(--text-muted)', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Product</th>
              <th style={{ padding: '0.75rem 1rem' }}>Stock Status</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Curr Stock</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Est. Demand</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Coverage</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Rec. Purchase</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Detail</th>
            </tr>
          </thead>
          <tbody>
            {dashboardData.reorder_suggestions.map((item) => (
              <tr key={item.product_id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '0.75rem 1rem', fontWeight: '600' }}>
                  {item.name}
                  <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.category}</span>
                </td>
                <td style={{ padding: '0.75rem 1rem' }}>
                  {getRiskBadge(item.stock_status)}
                </td>
                <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontWeight: '600' }}>
                  {item.current_stock}
                </td>
                <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                  {item.forecast_daily_demand} /day
                </td>
                <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontWeight: '600', color: item.days_of_stock < 3 ? 'var(--accent-amber)' : 'inherit' }}>
                  {item.days_of_stock !== null ? `${item.days_of_stock}d` : 'N/A'}
                </td>
                <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontWeight: '700', color: 'var(--accent-green)' }}>
                  {item.planning_suggestion.recommended_purchase > 0 ? `+${item.planning_suggestion.recommended_purchase} units` : 'Satisfied'}
                </td>
                <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                  <button
                    onClick={() => setSelectedProductId(item.product_id)}
                    style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer' }}
                  >
                    <Eye size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 5. Slow Moving Inventory Section */}
      {dashboardData.slow_moving_products.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '1.05rem', fontWeight: '600', marginBottom: '0.75rem', color: 'var(--accent-amber)' }}>
            ⚠️ Slow-Moving Inventory Alert
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem' }}>
            {dashboardData.slow_moving_products.map((item) => (
              <div key={item.product_id} style={{ background: '#0f172a', padding: '0.75rem', borderRadius: '0.5rem', border: '1px solid var(--border-color)' }}>
                <span style={{ fontWeight: '600', fontSize: '0.9rem', display: 'block' }}>{item.name}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Stock: <strong>{item.current_stock} units</strong> | Velocity: <strong>{item.velocity_per_day} /day</strong></span>
                <p style={{ fontSize: '0.78rem', color: 'var(--accent-amber)', marginTop: '0.3rem' }}>
                  {item.reason}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Product Analytics Detail Modal */}
      {selectedProductId && (
        <ProductAnalyticsModal
          productId={selectedProductId}
          onClose={() => setSelectedProductId(null)}
        />
      )}
    </div>
  )
}
