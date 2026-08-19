import { fetchWithAuth } from './lib/api';
import React, { useState, useEffect } from 'react'
import { Store, CheckCircle, Sun, Moon } from 'lucide-react'
import InventoryView from './components/InventoryView'
import CaptureView from './components/CaptureView'
import SalesHistoryView from './components/SalesHistoryView'
import DashboardView from './components/DashboardView'
import AdvisorView from './components/AdvisorView'
import LocalInsightsView from './components/LocalInsightsView'
import ReportsView from './components/ReportsView'
import Auth from './components/Auth'
import { supabase } from './lib/supabase'

export default function App() {
  const [session, setSession] = useState(null)
  const [activeTab, setActiveTab] = useState('Dashboard')
  const [healthStatus, setHealthStatus] = useState({ loading: true, data: null, error: null })
  const [products, setProducts] = useState([])
  const [theme, setTheme] = useState(() => localStorage.getItem('maruthi_theme') || 'dark')

  const [showDemoModal, setShowDemoModal] = useState(false);
  const [activeShop, setActiveShop] = useState(() => localStorage.getItem('maruthi_active_shop') || 'shop_001');

  const handleShopChange = (e) => {
    const newShopId = e.target.value;
    localStorage.setItem('maruthi_active_shop', newShopId);
    setActiveShop(newShopId);
    window.location.reload();
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('maruthi_theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'))
  }

  const fetchProducts = () => {
    fetchWithAuth('/api/products')
      .then(res => res.json())
      .then(data => setProducts(data))
      .catch(err => console.error('Products fetch error:', err))
  }

  useEffect(() => {
    fetchWithAuth('/api/health')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => setHealthStatus({ loading: false, data, error: null }))
      .catch(err => setHealthStatus({ loading: false, data: null, error: err.message }))

    fetchProducts()
  }, [])

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
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
          <h1 style={{ 
            fontSize: '1.75rem', 
            fontWeight: '800', 
            letterSpacing: '-0.025em',
            background: 'linear-gradient(to right, var(--accent-blue), var(--accent-purple))',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'inline-block'
          }}>MARUTHI</h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: '500' }}>AI Retail Copilot for Small Retailers</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          
          <select 
            value={activeShop} 
            onChange={handleShopChange}
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '0.5rem',
              border: '1px solid var(--border-color)',
              background: 'var(--card-bg)',
              color: 'var(--text-main)',
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            <option value="shop_001">Lakshmi Kirana (Grocery)</option>
            <option value="shop_002">Fashion Hub (Clothing)</option>
            <option value="shop_003">Ravi Hardware (Hardware)</option>
            <option value="shop_004">Sri Sai (General)</option>
          </select>
          <button
            onClick={() => setShowDemoModal(true)}
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '0.5rem',
              border: '1px solid var(--border-color)',
              background: 'transparent',
              color: 'var(--text-main)',
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            Demo Data
          </button>

          <div 
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
            style={{
              position: 'relative',
              width: '54px',
              height: '28px',
              borderRadius: '30px',
              background: theme === 'dark' ? '#1e293b' : '#e2e8f0',
              border: '1px solid var(--border-color)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 5px',
              transition: 'background 0.3s ease',
              boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.1)'
            }}
          >
            <Moon size={14} color={theme === 'dark' ? 'var(--text-muted)' : 'var(--accent-blue)'} style={{ zIndex: 1 }} />
            <Sun size={14} color={theme === 'dark' ? 'var(--accent-amber)' : 'var(--text-muted)'} style={{ zIndex: 1 }} />
            <div 
              style={{
                position: 'absolute',
                top: '2px',
                left: theme === 'dark' ? '28px' : '2px',
                width: '22px',
                height: '22px',
                background: theme === 'dark' ? '#0f172a' : '#ffffff',
                borderRadius: '50%',
                transition: 'left 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                zIndex: 2
              }}
            />
          </div>
          
          {session && (
            <button
              onClick={() => supabase.auth.signOut()}
              style={{
                padding: '0.4rem 0.8rem',
                borderRadius: '0.5rem',
                border: '1px solid var(--border-color)',
                background: 'transparent',
                color: 'var(--text-main)',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              Sign Out
            </button>
          )}

          <div className="badge" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Store size={14} /> Sri Lakshmi General Store (Ameerpet)
          </div>
        </div>
      </header>

      {/* Bypassed Auth for local development */}
      {false ? (
        <Auth onLogin={setSession} />
      ) : (
        <>
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
        </>
      )}

      {/* Demo Data Modal */}
      {showDemoModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.6)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="card" style={{ maxWidth: '500px', width: '90%', margin: '0 auto', background: 'var(--bg-main)' }}>
            <h3 style={{ marginTop: 0, fontSize: '1.25rem' }}>Reset Demo Data</h3>
            <p style={{ fontSize: '0.95rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              To ensure data safety, MARUTHI does not provide a one-click database reset via the UI. 
              To reset the application to its clean demo state, please run the setup script provided in the backend directory:
            </p>
            <div style={{ background: '#0f172a', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', border: '1px solid var(--border-color)', color: 'white', fontFamily: 'monospace' }}>
              &gt; cd backend <br/>
              &gt; ./setup.bat    <span style={{ color: 'var(--text-muted)' }}>// Windows</span><br/>
              &gt; ./setup.sh     <span style={{ color: 'var(--text-muted)' }}>// Mac/Linux</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setShowDemoModal(false)}
                style={{ padding: '0.5rem 1rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '600' }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer Health Check Bar */}
      <footer style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="status-box" style={{ 
            fontSize: '0.85rem', 
            padding: '0.4rem 0.8rem', 
            background: (!healthStatus.data || healthStatus.error) ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
            color: (!healthStatus.data || healthStatus.error) ? 'var(--accent-red)' : 'var(--accent-green)',
            border: `1px solid ${(!healthStatus.data || healthStatus.error) ? 'var(--accent-red)' : 'var(--accent-green)'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontWeight: '600'
          }}>
            {healthStatus.loading ? (
              <>⏳ Checking System Status...</>
            ) : (!healthStatus.data || healthStatus.error) ? (
              <>
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-red)' }}></span>
                🔴 Backend Offline: Please start the MARUTHI backend.
              </>
            ) : (
              <>
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-green)' }}></span>
                🟢 MARUTHI System Online (v{healthStatus.data.version})
              </>
            )}
        </div>
      </footer>
    </div>
  )
}
