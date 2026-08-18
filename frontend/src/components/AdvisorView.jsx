import React, { useState, useEffect } from 'react'
import { Bot, Send, AlertTriangle, TrendingUp, Package, CheckCircle, ShieldCheck, HelpCircle, Loader2 } from 'lucide-react'

export default function AdvisorView() {
  const [tomorrowPlan, setTomorrowPlan] = useState(null)
  const [loadingPlan, setLoadingPlan] = useState(true)
  const [planError, setPlanError] = useState(null)

  // Q&A Chat States
  const [question, setQuestion] = useState('')
  const [askLoading, setAskLoading] = useState(false)
  const [qaHistory, setQaHistory] = useState([])
  const [askError, setAskError] = useState(null)

  const fetchTomorrowPlan = async () => {
    try {
      setLoadingPlan(true)
      const res = await fetch('/api/advisor/tomorrow')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setTomorrowPlan(data)
      setPlanError(null)
    } catch (err) {
      setPlanError(err.message)
    } finally {
      setLoadingPlan(false)
    }
  }

  useEffect(() => {
    fetchTomorrowPlan()
  }, [])

  const handleAskQuestion = async (customQ = question) => {
    const qToSubmit = (typeof customQ === 'string' ? customQ : question).trim()
    if (!qToSubmit) return

    try {
      setAskLoading(true)
      setAskError(null)

      const res = await fetch('/api/advisor/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shop_id: 'shop_001', question: qToSubmit })
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to get answer')
      }

      const data = await res.json()
      setQaHistory(prev => [data, ...prev])
      setQuestion('')
    } catch (err) {
      setAskError(err.message)
    } finally {
      setAskLoading(false)
    }
  }

  const getCategoryBadge = (cat) => {
    if (cat === 'URGENT_REORDER') {
      return <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><AlertTriangle size={12} /> URGENT REORDER</span>
    }
    if (cat === 'PROFIT_OPPORTUNITY') {
      return <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><TrendingUp size={12} /> PROFIT FOCUS</span>
    }
    return <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '700', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><Package size={12} /> SLOW MOVING</span>
  }

  return (
    <div>
      {/* Advisor Header & Mode Badge */}
      <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
            <Bot size={22} style={{ color: 'var(--accent-blue)' }} />
            <h2 style={{ fontSize: '1.3rem', fontWeight: '700' }}>AI Business Advisor</h2>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            READ-ONLY Grounded Business Intelligence & Action Plans. Verified evidence based on database facts.
          </p>
        </div>

        {tomorrowPlan && (
          <span style={{ padding: '0.35rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.8rem', background: tomorrowPlan.mode === 'ai_grounded' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(245, 158, 11, 0.15)', color: tomorrowPlan.mode === 'ai_grounded' ? 'var(--accent-blue)' : 'var(--accent-amber)', border: '1px solid var(--border-color)', fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
            {tomorrowPlan.mode === 'ai_grounded' ? '🤖 Gemini AI Grounded Advisor' : '⚙️ Deterministic Advisor Engine'}
          </span>
        )}
      </div>

      {/* Section 1: Tomorrow's Prioritized Action Plan */}
      <div style={{ marginBottom: '2rem' }}>
        <h3 style={{ fontSize: '1.15rem', fontWeight: '600', marginBottom: '1rem' }}>
          📅 Tomorrow's Prioritized Action Plan
        </h3>

        {loadingPlan ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Collecting verified store evidence & building plan...</div>
        ) : planError ? (
          <div style={{ color: 'var(--accent-red)', padding: '1rem' }}>Failed to load action plan: {planError}</div>
        ) : tomorrowPlan?.recommendations ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {tomorrowPlan.recommendations.map((rec) => (
              <div key={rec.priority} className="card" style={{ marginBottom: 0, borderLeft: `4px solid ${rec.category === 'URGENT_REORDER' ? 'var(--accent-red)' : rec.category === 'PROFIT_OPPORTUNITY' ? 'var(--accent-green)' : 'var(--accent-amber)'}` }}>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span style={{ width: '26px', height: '26px', borderRadius: '50%', background: '#0f172a', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '700', fontSize: '0.85rem' }}>
                      #{rec.priority}
                    </span>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: '700' }}>{rec.title}</h4>
                  </div>
                  {getCategoryBadge(rec.category)}
                </div>

                {/* RECOMMENDATION Statement */}
                <div style={{ background: '#0f172a', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1rem', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.2rem' }}>
                    💡 RECOMMENDATION
                  </span>
                  <p style={{ fontSize: '0.9rem', color: 'white', fontWeight: '500', margin: 0 }}>
                    {rec.recommendation_summary}
                  </p>
                </div>

                {/* FACT Grid (Verified Database Values) */}
                {rec.facts && rec.facts.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.4rem' }}>
                      ✓ VERIFIED DATABASE FACTS
                    </span>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.5rem' }}>
                      {rec.facts.map((fact, idx) => (
                        <div key={idx} style={{ background: 'var(--bg-card)', padding: '0.5rem 0.75rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', fontSize: '0.82rem' }}>
                          <span style={{ color: 'var(--text-muted)', display: 'block', fontSize: '0.75rem' }}>{fact.field_name}</span>
                          <strong style={{ color: 'var(--text-main)' }}>{fact.value_str}</strong>
                          <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>Source: {fact.source_entity}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Steps */}
                {rec.action_steps && rec.action_steps.length > 0 && (
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.3rem' }}>
                      Action Steps for Tomorrow:
                    </span>
                    <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      {rec.action_steps.map((step, idx) => (
                        <li key={idx} style={{ marginBottom: '0.2rem' }}>{step}</li>
                      ))}
                    </ul>
                  </div>
                )}

              </div>
            ))}
          </div>
        ) : null}
      </div>

      {/* Section 2: Interactive Q&A Chat */}
      <div className="card">
        <h3 style={{ fontSize: '1.15rem', fontWeight: '600', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          💬 Ask AI Business Advisor
        </h3>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Ask any question about your shop's stock, revenue, margins, or reorder priorities.
        </p>

        {/* Question Shortcuts */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
          {[
            'What should I reorder tomorrow?',
            'How is my profit margin today?',
            'Which items are slow moving?'
          ].map(shortcut => (
            <button
              key={shortcut}
              onClick={() => handleAskQuestion(shortcut)}
              disabled={askLoading}
              style={{ padding: '0.35rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', color: 'var(--accent-blue)', borderRadius: '1rem', fontSize: '0.8rem', fontWeight: '500', cursor: 'pointer' }}
            >
              "{shortcut}"
            </button>
          ))}
        </div>

        {askError && (
          <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.5rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {askError}
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAskQuestion()}
            placeholder="e.g. Which items should I order tomorrow?"
            style={{ flex: 1, padding: '0.65rem 0.85rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.5rem', color: 'white', fontSize: '0.9rem' }}
          />
          <button
            onClick={() => handleAskQuestion()}
            disabled={askLoading || !question.trim()}
            style={{ padding: '0.65rem 1.25rem', background: askLoading || !question.trim() ? 'var(--border-color)' : 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.5rem', fontWeight: '600', cursor: askLoading || !question.trim() ? 'not-allowed' : 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}
          >
            {askLoading ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
            Ask
          </button>
        </div>

        {/* Q&A Responses List */}
        {qaHistory.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {qaHistory.map((qa, idx) => (
              <div key={idx} style={{ background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.5rem', padding: '1rem' }}>
                <div style={{ fontWeight: '600', color: 'var(--accent-blue)', fontSize: '0.9rem', marginBottom: '0.4rem' }}>
                  Q: "{qa.question}"
                </div>

                <div style={{ fontSize: '0.95rem', color: 'white', marginBottom: '0.75rem', lineHeight: '1.5' }}>
                  {qa.answer}
                </div>

                {/* Grounded Facts Table */}
                {qa.grounded_facts && qa.grounded_facts.length > 0 && (
                  <div style={{ marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--accent-green)', fontWeight: '700', display: 'block', marginBottom: '0.3rem' }}>
                      ✓ GROUNDED EVIDENCE FACTS:
                    </span>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                      {qa.grounded_facts.map((fact, fIdx) => (
                        <div key={fIdx} style={{ background: 'var(--bg-card)', padding: '0.3rem 0.6rem', borderRadius: '0.375rem', border: '1px solid var(--border-color)', fontSize: '0.78rem' }}>
                          <strong>{fact.field_name}:</strong> {fact.value_str}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
