import { fetchWithAuth } from '../lib/api';
import React, { useState } from 'react'
import { Camera, Mic, Edit3, UploadCloud, AlertCircle, CheckCircle2, Loader2, FileText, ShoppingBag } from 'lucide-react'
import InvoiceReview from './InvoiceReview'
import SaleReview from './SaleReview'
import ManualSaleForm from './ManualSaleForm'
import BulkImportView from './BulkImportView'

export default function CaptureView({ products, onPurchaseConfirmed }) {
  const [activeMode, setActiveMode] = useState('sales') // 'sales' or 'invoice'
  const [salesSubMode, setSalesSubMode] = useState('natural') // 'natural' or 'manual'

  // Invoice States
  const [extractionResult, setExtractionResult] = useState(null)
  const [invoiceLoading, setInvoiceLoading] = useState(false)
  const [invoiceLoadingStep, setInvoiceLoadingStep] = useState('')

  // Sales States
  const [salesText, setSalesText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [speechWarning, setSpeechWarning] = useState(null)
  const [saleParseResult, setSaleParseResult] = useState(null)
  const [salesLoading, setSalesLoading] = useState(false)

  const [error, setError] = useState(null)
  const [successFeedback, setSuccessFeedback] = useState(null)

  // 1. Voice Speech Recognition Handler
  const startVoiceRecording = () => {
    setSpeechWarning(null)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      setSpeechWarning("Voice recognition is not supported in this browser. Please use text input or manual sale entry.")
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognition.continuous = false
      recognition.interimResults = false
      recognition.lang = 'en-IN'

      recognition.onstart = () => {
        setIsListening(true)
      }

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setSalesText(transcript)
        setIsListening(false)
        handleParseSaleText(transcript)
      }

      recognition.onerror = (event) => {
        setIsListening(false)
        setSpeechWarning(`Voice error: ${event.error}. Please type the sale instead.`)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognition.start()
    } catch (err) {
      setIsListening(false)
      setSpeechWarning("Voice input initialization failed. Please type the sale instead.")
    }
  }

  // 2. Natural Sales Parse Handler
  const handleParseSaleText = async (textToParse = salesText) => {
    if (!textToParse || !textToParse.trim()) {
      setError('Please speak or enter sale text (e.g. "Sold 3 Coke and 2 Lays").')
      return
    }

    try {
      setSalesLoading(true)
      setError(null)
      setSuccessFeedback(null)

      const res = await fetchWithAuth('/api/sales/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shop_id: 'shop_001', text: textToParse.trim() })
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to parse sale text')
      }

      const data = await res.json()
      setSaleParseResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setSalesLoading(false)
    }
  }

  // 3. Invoice Upload Handler
  const handleInvoiceUpload = async (file) => {
    if (!file) return

    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|webp)$/i)) {
      setError('Unsupported file type. Please upload a JPEG, PNG, or WebP invoice image.')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds 10MB limit. Please upload a smaller image.')
      return
    }

    try {
      setInvoiceLoading(true)
      setError(null)
      setSuccessFeedback(null)

      setInvoiceLoadingStep('Uploading invoice photo...')
      await new Promise(r => setTimeout(r, 300))

      setInvoiceLoadingStep('Reading invoice with Vision AI / OCR...')
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetchWithAuth('/api/purchases/invoice', {
        method: 'POST',
        body: formData
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Invoice processing failed')
      }

      const data = await res.json()
      setExtractionResult(data)
    } catch (err) {
      setError(err.message || 'Invoice could not be read clearly. Try a brighter photo or upload a clearer image.')
    } finally {
      setInvoiceLoading(false)
      setInvoiceLoadingStep('')
    }
  }

  const handleSaleConfirmed = (res) => {
    setSaleParseResult(null)
    setSalesSubMode('natural')
    setSalesText('')
    setSuccessFeedback(`Sale #${res.id} confirmed! Revenue: ₹${res.total_amount}, Profit: ₹${res.profit} (${res.margin_pct}% margin). Inventory updated.`)
    if (onPurchaseConfirmed) onPurchaseConfirmed()
  }

  const handleInvoiceConfirmed = (res) => {
    setExtractionResult(null)
    setSuccessFeedback(`Stock update successful! Purchase record #${res.purchase_id} created with ${res.updated_inventories?.length || 0} inventory updates.`)
    if (onPurchaseConfirmed) onPurchaseConfirmed()
  }

  // Render Sub-Views if in Review or Manual Mode
  if (extractionResult) {
    return (
      <InvoiceReview
        extractionData={extractionResult}
        products={products}
        onConfirmSuccess={handleInvoiceConfirmed}
        onBack={() => setExtractionResult(null)}
      />
    )
  }

  if (saleParseResult) {
    return (
      <SaleReview
        parseData={saleParseResult}
        products={products}
        onConfirmSuccess={handleSaleConfirmed}
        onBack={() => setSaleParseResult(null)}
      />
    )
  }

  if (salesSubMode === 'manual') {
    return (
      <ManualSaleForm
        products={products}
        onConfirmSuccess={handleSaleConfirmed}
        onBack={() => setSalesSubMode('natural')}
      />
    )
  }

  return (
    <div>
      {/* Top Mode Selector Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveMode('sales')}
          style={{ flex: 1, padding: '0.75rem', borderRadius: '0.5rem', background: activeMode === 'sales' ? 'var(--accent-blue)' : 'var(--bg-card)', color: activeMode === 'sales' ? 'white' : 'var(--text-muted)', border: '1px solid var(--border-color)', fontWeight: '600', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
        >
          <ShoppingBag size={18} /> Record Sale (Voice / Text)
        </button>
        <button
          onClick={() => setActiveMode('invoice')}
          style={{ flex: 1, padding: '0.75rem', borderRadius: '0.5rem', background: activeMode === 'invoice' ? 'var(--accent-blue)' : 'var(--bg-card)', color: activeMode === 'invoice' ? 'white' : 'var(--text-muted)', border: '1px solid var(--border-color)', fontWeight: '600', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
        >
          <Camera size={18} /> Add Stock from Invoice
        </button>
        <button
          onClick={() => setActiveMode('bulk_import')}
          style={{ flex: 1, padding: '0.75rem', borderRadius: '0.5rem', background: activeMode === 'bulk_import' ? 'var(--accent-blue)' : 'var(--bg-card)', color: activeMode === 'bulk_import' ? 'white' : 'var(--text-muted)', border: '1px solid var(--border-color)', fontWeight: '600', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
        >
          <UploadCloud size={18} /> Bulk Import (CSV)
        </button>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {successFeedback && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid var(--accent-green)', color: 'var(--accent-green)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={18} />
          <span style={{ fontWeight: '500' }}>{successFeedback}</span>
        </div>
      )}

      {/* Mode 1: Natural Sales Capture (Voice, Text, Manual) */}
      {activeMode === 'sales' && (
        <div className="card" style={{ padding: '2rem 1.5rem', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '0.5rem' }}>Natural Sales Capture</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Speak, type, or enter line items manually. Server calculates revenue, profit, and margin deterministically from database prices.
          </p>

          {speechWarning && (
            <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid var(--accent-amber)', color: 'var(--accent-amber)', padding: '0.5rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.85rem', marginBottom: '1.5rem', textAlign: 'left' }}>
              ⚠️ {speechWarning}
            </div>
          )}

          {/* Voice Microphone Capture Button */}
          <div style={{ marginBottom: '1.5rem' }}>
            <button
              onClick={startVoiceRecording}
              disabled={isListening || salesLoading}
              style={{
                width: '80px', height: '80px', borderRadius: '50%',
                background: isListening ? 'var(--accent-red)' : 'var(--accent-blue)',
                border: 'none', color: 'white', display: 'inline-flex',
                alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
                boxShadow: isListening ? '0 0 20px rgba(239, 68, 68, 0.6)' : '0 4px 12px rgba(59, 130, 246, 0.4)',
                transition: 'all 0.2s ease'
              }}
            >
              <Mic size={36} className={isListening ? 'spin' : ''} />
            </button>
            <p style={{ fontSize: '0.85rem', color: isListening ? 'var(--accent-red)' : 'var(--text-muted)', marginTop: '0.5rem', fontWeight: '500' }}>
              {isListening ? 'Listening... Speak now (e.g. "Sold 3 Coke and 2 Lays")' : 'Tap microphone to speak sale'}
            </p>
          </div>

          <div style={{ margin: '1rem 0', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: '600' }}>OR</div>

          {/* Natural Language Text Box */}
          <div style={{ maxWidth: '550px', margin: '0 auto 1.5rem' }}>
            <textarea
              rows={2}
              value={salesText}
              onChange={e => setSalesText(e.target.value)}
              placeholder='e.g. "Sold 3 Coke, 2 Lays and one Dairy Milk"'
              style={{ width: '100%', padding: '0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.5rem', color: 'white', resize: 'vertical', fontFamily: 'inherit', marginBottom: '0.75rem' }}
            />
            <button
              onClick={() => handleParseSaleText()}
              disabled={salesLoading}
              style={{ width: '100%', padding: '0.65rem', background: 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.375rem', fontWeight: '600', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
            >
              {salesLoading ? <Loader2 size={16} className="spin" /> : <Edit3 size={16} />}
              {salesLoading ? 'Parsing Sale...' : 'Parse Sale Text'}
            </button>
          </div>

          <div style={{ margin: '1rem 0', color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: '600' }}>OR</div>

          {/* Manual Sales Entry Button */}
          <button
            onClick={() => setSalesSubMode('manual')}
            style={{ padding: '0.6rem 1.25rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-main)', borderRadius: '0.375rem', fontWeight: '500', cursor: 'pointer' }}
          >
            🧾 Enter Sale Manually
          </button>
        </div>
      )}

      {/* Mode 2: Invoice Stock Upload */}
      {activeMode === 'invoice' && (
        <div className="card" style={{ padding: '2rem 1.5rem', textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.15)', border: '1px solid var(--accent-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}>
            <Camera size={32} style={{ color: 'var(--accent-blue)' }} />
          </div>

          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '0.5rem' }}>📸 Add Stock from Invoice</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
            Photograph or upload any paper invoice. Vision AI extracts items and matches products for review.
          </p>

          {invoiceLoading ? (
            <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
              <Loader2 size={36} className="spin" style={{ color: 'var(--accent-blue)' }} />
              <p style={{ fontWeight: '500', color: 'var(--text-main)' }}>{invoiceLoadingStep}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '1rem' }}>
              <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem', background: 'var(--accent-blue)', color: 'white', borderRadius: '0.5rem', fontWeight: '600', cursor: 'pointer' }}>
                <Camera size={20} /> Take Photo / Camera
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={e => e.target.files?.[0] && handleInvoiceUpload(e.target.files[0])}
                  style={{ display: 'none' }}
                />
              </label>

              <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem', background: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-main)', borderRadius: '0.5rem', fontWeight: '500', cursor: 'pointer' }}>
                <UploadCloud size={20} /> Browse File / Gallery
                <input
                  type="file"
                  accept="image/jpeg,image/jpg,image/png,image/webp"
                  onChange={e => e.target.files?.[0] && handleInvoiceUpload(e.target.files[0])}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          )}
        </div>
      )}

      {/* Mode 3: Bulk Import */}
      {activeMode === 'bulk_import' && (
        <BulkImportView onImportComplete={onPurchaseConfirmed} />
      )}
    </div>
  )
}
