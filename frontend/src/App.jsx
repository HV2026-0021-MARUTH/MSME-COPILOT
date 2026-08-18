import React, { useState, useEffect } from 'react'
import { Store, CheckCircle, Sun, Moon } from 'lucide-react'
import InventoryView from './components/InventoryView'
import CaptureView from './components/CaptureView'
import SalesHistoryView from './components/SalesHistoryView'
import DashboardView from './components/DashboardView'
import AdvisorView from './components/AdvisorView'
import LocalInsightsView from './components/LocalInsightsView'
import ReportsView from './components/ReportsView'

export default function App() {
  const [activeTab, setActiveTab] = useState('Dashboard')
  const [healthStatus, setHealthStatus] = useState({ loading: true, data: null, error: null })
  const [products, setProducts] = useState([])
  const [theme, setTheme] = useState(() => localStorage.getItem('maruthi_theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('maruthi_theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
  }

  const fetchProducts = () => {
    fetch('/api/products')
      .then(res => res.json())
      .then(data => setProducts(data))
      .catch(err => console.error('Products fetch error:', err))
  }

  useEffect(() => {
    fetch('/api/health')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => setHealthStatus({ loading: false, data, error: null }))
      .catch(err => setHealthStatus({ loading: false, data: null, error: err.message }))

    fetchProducts()
  }, [])

  const handleStockOrSaleConfirmed = () => {
    fetchProducts()
  }

  const tabs = [
    'Dashboard', 'Capture', 'Inventory', 'Sales',
    'Forecast', 'AI Advisor', 'Local Insights', 'Reports'
  ]

  return (
    <div className="container">
      <header>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>MARUTHI</h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>AI Retail Copilot for Small Retailers</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.4rem 0.8rem',
              borderRadius: '0.5rem',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-card)',
              color: 'var(--text-main)',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: '500'
            }}
          >
            {theme === 'dark' ? <Sun size={15} color="var(--accent-amber)" /> : <Moon size={15} color="var(--accent-blue)" />}
            <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
          <div className="badge" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Store size={14} /> Sri Lakshmi General Store (Ameerpet)
          </div>
        </div>
      </header>

      <div className="nav-tabs">
        {tabs.map(tab => (
          <button
            key={tab}
            className={`nav-tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => {
              setActiveTab(tab)
              if (tab === 'Capture' || tab === 'Inventory') fetchProducts()
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {(activeTab === 'Dashboard' || activeTab === 'Forecast') && (
        <DashboardView />
      )}

      {activeTab === 'Capture' && (
        <CaptureView products={products} onPurchaseConfirmed={handleStockOrSaleConfirmed} />
      )}

      {activeTab === 'Inventory' && (
        <InventoryView onInventoryChange={handleStockOrSaleConfirmed} />
      )}

      {activeTab === 'Sales' && (
        <SalesHistoryView />
      )}

      {activeTab === 'AI Advisor' && (
        <AdvisorView />
      )}

      {activeTab === 'Local Insights' && (
        <LocalInsightsView />
      )}

      {activeTab === 'Reports' && (
        <ReportsView />
      )}

      {/* Footer Health Check Bar */}
      <footer style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {healthStatus.data && (
          <div className="status-box" style={{ fontSize: '0.8rem', padding: '0.25rem 0.6rem' }}>
            <CheckCircle size={12} /> Backend Status: {healthStatus.data.status} (v{healthStatus.data.version})
          </div>
        )}
      </footer>
    </div>
  )
}
