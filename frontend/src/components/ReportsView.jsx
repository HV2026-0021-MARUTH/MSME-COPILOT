import React, { useState } from 'react'
import { FileText, Table, Image, Download, CheckCircle, ShieldCheck, Calendar, Loader2 } from 'lucide-react'

export default function ReportsView() {
  const [selectedPeriod, setSelectedPeriod] = useState('7d')
  const [downloadingFormat, setDownloadingFormat] = useState(null)
  const [statusMsg, setStatusMsg] = useState(null)

  const handleDownload = async (format) => {
    try {
      setDownloadingFormat(format)
      setStatusMsg(`Generating verified MARUTHI ${format.toUpperCase()} report...`)

      const url = `/api/reports/business/${format}?period=${selectedPeriod}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to generate ${format} report`)
      }

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `maruthi_business_report_${selectedPeriod}.${format}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(downloadUrl)

      setStatusMsg(`✓ ${format.toUpperCase()} report downloaded successfully!`)
    } catch (err) {
      console.error("Report generation error:", err)
      const isConnectionErr = err.message && (err.message.includes('fetch') || err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))
      const userMsg = isConnectionErr
        ? "Unable to connect to MARUTHI server. Please ensure the backend is running."
        : (err.message || "Failed to generate report")
      setStatusMsg(`❌ ${userMsg}`)
    } finally {
      setDownloadingFormat(null)
    }
  }

  const periods = [
    { code: 'today', label: 'Today' },
    { code: '7d', label: 'Last 7 Days' },
    { code: '30d', label: 'Last 30 Days' }
  ]

  return (
    <div>
      {/* Header */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={22} style={{ color: 'var(--accent-blue)' }} /> Business Reports & Export
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Generate verified business reports in PDF, Excel, and PNG snapshot formats.
            </p>
          </div>

          <div className="status-box" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid var(--accent-green)', color: 'var(--accent-green)' }}>
            <ShieldCheck size={14} /> 100% Read-Only Safety Guaranteed
          </div>
        </div>
      </div>

      {/* Period Selection Bar */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '0.6rem' }}>
          Select Report Period:
        </span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {periods.map(p => (
            <button
              key={p.code}
              onClick={() => setSelectedPeriod(p.code)}
              style={{
                padding: '0.55rem 1.25rem',
                borderRadius: '0.5rem',
                fontSize: '0.88rem',
                fontWeight: '600',
                cursor: 'pointer',
                border: '1px solid var(--border-color)',
                background: selectedPeriod === p.code ? 'var(--accent-blue)' : '#0f172a',
                color: 'white',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              <Calendar size={14} /> {p.label}
            </button>
          ))}
        </div>
      </div>

      {statusMsg && (
        <div style={{ padding: '0.75rem 1rem', background: statusMsg.startsWith('✓') ? 'rgba(16, 185, 129, 0.15)' : statusMsg.startsWith('❌') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(59, 130, 246, 0.15)', border: '1px solid var(--border-color)', color: 'white', borderRadius: '0.5rem', marginBottom: '1.5rem', fontSize: '0.88rem' }}>
          {statusMsg}
        </div>
      )}

      {/* Download Format Cards (Grid) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
        
        {/* PDF Card */}
        <div className="card" style={{ marginBottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <FileText size={24} style={{ color: 'var(--accent-red)' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Full Business Report</h3>
            </div>
            <span style={{ fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', fontWeight: '700' }}>PDF DOCUMENT</span>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.75rem', lineHeight: '1.4' }}>
              Clean, professional multi-page document with Business Summary, Sales Trends, Inventory Health, Forecasts, and AI Advisor guidance.
            </p>
          </div>

          <button
            onClick={() => handleDownload('pdf')}
            disabled={downloadingFormat === 'pdf'}
            style={{ marginTop: '1.25rem', width: '100%', padding: '0.65rem', background: 'var(--accent-red)', border: 'none', color: 'white', borderRadius: '0.5rem', fontWeight: '600', cursor: downloadingFormat === 'pdf' ? 'not-allowed' : 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', fontSize: '0.9rem' }}
          >
            {downloadingFormat === 'pdf' ? <Loader2 size={16} className="spin" /> : <Download size={16} />}
            {downloadingFormat === 'pdf' ? 'Generating PDF...' : '📄 Download PDF'}
          </button>
        </div>

        {/* Excel XLSX Card */}
        <div className="card" style={{ marginBottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Table size={24} style={{ color: 'var(--accent-green)' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Detailed Data Workbook</h3>
            </div>
            <span style={{ fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', fontWeight: '700' }}>EXCEL XLSX (7 SHEETS)</span>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.75rem', lineHeight: '1.4' }}>
              Structured Excel workbook containing 7 distinct sheets with frozen header rows, formatted numbers, and full line item details.
            </p>
          </div>

          <button
            onClick={() => handleDownload('xlsx')}
            disabled={downloadingFormat === 'xlsx'}
            style={{ marginTop: '1.25rem', width: '100%', padding: '0.65rem', background: 'var(--accent-green)', border: 'none', color: 'white', borderRadius: '0.5rem', fontWeight: '600', cursor: downloadingFormat === 'xlsx' ? 'not-allowed' : 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', fontSize: '0.9rem' }}
          >
            {downloadingFormat === 'xlsx' ? <Loader2 size={16} className="spin" /> : <Download size={16} />}
            {downloadingFormat === 'xlsx' ? 'Generating Excel...' : '📊 Download Excel'}
          </button>
        </div>

        {/* PNG Card */}
        <div className="card" style={{ marginBottom: 0, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Image size={24} style={{ color: 'var(--accent-blue)' }} />
              <h3 style={{ fontSize: '1.1rem', fontWeight: '700' }}>Share Snapshot Card</h3>
            </div>
            <span style={{ fontSize: '0.75rem', background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-blue)', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', fontWeight: '700' }}>PNG IMAGE (WHATSAPP/MOBILE)</span>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.75rem', lineHeight: '1.4' }}>
              Single shareable 1080px executive summary image card featuring key metrics, top sellers, and tomorrow's priority action.
            </p>
          </div>

          <button
            onClick={() => handleDownload('png')}
            disabled={downloadingFormat === 'png'}
            style={{ marginTop: '1.25rem', width: '100%', padding: '0.65rem', background: 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.5rem', fontWeight: '600', cursor: downloadingFormat === 'png' ? 'not-allowed' : 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', fontSize: '0.9rem' }}
          >
            {downloadingFormat === 'png' ? <Loader2 size={16} className="spin" /> : <Download size={16} />}
            {downloadingFormat === 'png' ? 'Generating PNG...' : '🖼️ Download PNG'}
          </button>
        </div>

      </div>

      {/* Data Consistency Banner */}
      <div className="card" style={{ background: '#0f172a', border: '1px solid var(--border-color)' }}>
        <h4 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'white', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <CheckCircle size={16} style={{ color: 'var(--accent-green)' }} /> Verified MARUTHI Business Data Guarantee
        </h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
          All three report formats (PDF, Excel, PNG) consume the exact same centralized report data pipeline. Revenue, Profit, Margin %, and Inventory Values are 100% consistent across every export format.
        </p>
      </div>
    </div>
  )
}
