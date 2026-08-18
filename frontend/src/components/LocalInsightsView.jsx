import { fetchWithAuth } from '../lib/api';
import React, { useState, useEffect } from 'react'
import { MapPin, Calendar, Sun, CloudRain, AlertOctagon, TrendingUp, Package, ShieldCheck, Search, Loader2 } from 'lucide-react'

export default function LocalInsightsView() {
  const [localityInput, setLocalityInput] = useState('')
  const [activeLocation, setActiveLocation] = useState({ lat: null, lon: null, name: 'Detecting Location...' })
  const [intelligence, setIntelligence] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [gpsLoading, setGpsLoading] = useState(false)

  const fetchIntelligence = async (lat = null, lon = null, manual = null) => {
    try {
      setLoading(true)
      const res = await fetchWithAuth('/api/intelligence/local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: lat,
          longitude: lon,
          locality_input: manual
        })
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setIntelligence(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIntelligence(null, null, null)
  }, [])

  // Tier 1: Browser GPS Handler
  const handleGPSDetect = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser. Using manual locality entry instead.")
      return
    }

    setGpsLoading(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsLoading(false)
        fetchIntelligence(pos.coords.latitude, pos.coords.longitude, null)
      },
      (err) => {
        setGpsLoading(false)
        setError(`GPS permission denied or unavailable (${err.message}). Defaulting to shop location.`)
        fetchIntelligence(null, null, null)
      },
      { timeout: 8000 }
    )
  }

  // Tier 2: Manual Input Handler
  const handleManualSubmit = (e) => {
    e.preventDefault()
    if (!localityInput.trim()) return
    fetchIntelligence(null, null, localityInput.trim())
  }

  const getCategoryBadge = (cat) => {
    if (cat === 'SELL_MORE') {
      return <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-blue)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><TrendingUp size={12} /> WHAT MAY SELL MORE</span>
    }
    if (cat === 'WHAT_TO_STOCK') {
      return <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><Package size={12} /> WHAT TO STOCK</span>
    }
    return <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><AlertOctagon size={12} /> AVOID OVERSTOCKING</span>
  }

  return (
    <div>
      {/* Location Control Bar (3-Tier Location Resolution) */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <MapPin size={22} style={{ color: 'var(--accent-blue)' }} /> Local & Seasonal Intelligence
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Grounded retail insights combining local signals with MARUTHI internal store data.
            </p>
          </div>

          <button
            onClick={handleGPSDetect}
            disabled={gpsLoading}
            style={{ padding: '0.6rem 1.1rem', background: 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.5rem', fontWeight: '600', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem' }}
          >
            {gpsLoading ? <Loader2 size={16} className="spin" /> : <MapPin size={16} />}
            {gpsLoading ? 'Locating...' : '📍 Detect My Location (GPS)'}
          </button>
        </div>

        {/* Manual Locality Search Form */}
        <form onSubmit={handleManualSubmit} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <input
            type="text"
            value={localityInput}
            onChange={e => setLocalityInput(e.target.value)}
            placeholder='Or enter locality manually (e.g. "Ameerpet, Hyderabad" or "Koramangala, Bengaluru")'
            style={{ flex: 1, padding: '0.6rem 0.85rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white', fontSize: '0.88rem' }}
          />
          <button
            type="submit"
            style={{ padding: '0.6rem 1.1rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-main)', borderRadius: '0.375rem', fontWeight: '600', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.88rem' }}
          >
            <Search size={16} /> Apply Locality
          </button>
        </form>

        {/* Active Resolved Location Badge */}
        {intelligence && (
          <div style={{ background: '#0f172a', padding: '0.5rem 0.75rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', fontSize: '0.82rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Location Context: <strong style={{ color: 'var(--accent-blue)' }}>{intelligence.resolved_location_name}</strong></span>
            <span style={{ color: 'var(--text-muted)' }}>Source: <strong style={{ color: 'var(--accent-green)' }}>{intelligence.location_source}</strong></span>
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid var(--accent-amber)', color: 'var(--accent-amber)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', fontSize: '0.88rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Active Season & Festival Banner */}
      {intelligence && (
        <div className="card" style={{ marginBottom: '1.5rem', background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: '700' }}>Seasonal Signals</span>
              <h3 style={{ fontSize: '1.2rem', fontWeight: '700', marginTop: '0.2rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Sun size={20} style={{ color: 'var(--accent-amber)' }} /> {intelligence.current_season}
              </h3>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Upcoming Festivals</span>
              <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.2rem' }}>
                {intelligence.upcoming_festivals.map((fest, idx) => (
                  <span key={idx} style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.8rem', background: '#0f172a', border: '1px solid var(--border-color)', color: 'var(--accent-green)', fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Calendar size={12} /> {fest}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recommendations List with 3 Evidence Levels */}
      {loading ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Resolving local intelligence signals & store data...</div>
      ) : intelligence?.recommendations ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {intelligence.recommendations.map((rec, idx) => (
            <div key={idx} className="card" style={{ marginBottom: 0 }}>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h4 style={{ fontSize: '1.05rem', fontWeight: '700' }}>{rec.title}</h4>
                {getCategoryBadge(rec.category)}
              </div>

              {/* Level 1: RECOMMENDATION Statement */}
              <div style={{ background: '#0f172a', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1rem', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.2rem' }}>
                  💡 RECOMMENDATION
                </span>
                <p style={{ fontSize: '0.9rem', color: 'white', fontWeight: '600', margin: 0 }}>
                  {rec.recommendation_summary}
                </p>
                <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)', marginTop: '0.4rem', marginBottom: 0 }}>
                  <strong>Why MARUTHI Recommends This:</strong> {rec.why_reason}
                </p>
              </div>

              {/* Level 2: FACT Grid (Verified Internal DB Data) */}
              {rec.facts && rec.facts.length > 0 && (
                <div style={{ marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.3rem' }}>
                    [FACT] Verified MARUTHI Store Data:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {rec.facts.map((fact, fIdx) => (
                      <div key={fIdx} style={{ background: 'var(--bg-card)', padding: '0.4rem 0.65rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>{fact.field_name}: </span>
                        <strong style={{ color: 'var(--text-main)' }}>{fact.value_str}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Level 3: SIGNAL Grid (Verified External Signals) */}
              {rec.signals && rec.signals.length > 0 && (
                <div style={{ marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--accent-amber)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.3rem' }}>
                    [SIGNAL] Verified External & Locality Drivers:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {rec.signals.map((sig, sIdx) => (
                      <div key={sIdx} style={{ background: 'var(--bg-card)', padding: '0.4rem 0.65rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>{sig.category}: </span>
                        <strong style={{ color: 'var(--text-main)' }}>{sig.description}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Steps */}
              {rec.action_steps && rec.action_steps.length > 0 && (
                <div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.2rem' }}>
                    Suggested Action Steps:
                  </span>
                  <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    {rec.action_steps.map((step, sIdx) => (
                      <li key={sIdx}>{step}</li>
                    ))}
                  </ul>
                </div>
              )}

            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}
