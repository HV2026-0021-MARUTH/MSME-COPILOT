import { fetchWithAuth } from '../lib/api';
import React, { useState } from 'react'
import { CheckCircle, AlertTriangle, Trash2, Plus, ArrowLeft, ShieldCheck, Cpu } from 'lucide-react'
import ProductFormModal from './ProductFormModal'

export default function InvoiceReview({ extractionData, products, onConfirmSuccess, onBack }) {
  const [supplierName, setSupplierName] = useState(extractionData.supplier || 'Supplier')
  const [invoiceNumber, setInvoiceNumber] = useState(extractionData.invoice_number || '')
  const [invoiceDate, setInvoiceDate] = useState(extractionData.invoice_date || '')
  const [items, setItems] = useState(extractionData.items || [])
  const [error, setError] = useState(null)
  const [isConfirming, setIsConfirming] = useState(false)

  // New product creation state
  const [isProductModalOpen, setIsProductModalOpen] = useState(false)
  const [targetItemIndex, setTargetItemIndex] = useState(null)

  const handleItemChange = (index, field, value) => {
    const updated = [...items]
    updated[index][field] = value

    if (field === 'quantity' || field === 'unit_cost') {
      const q = Number(updated[index].quantity) || 0
      const c = Number(updated[index].unit_cost) || 0
      updated[index].total = roundVal(q * c)
    }
    setItems(updated)
  }

  const roundVal = (val) => Math.round(val * 100) / 100

  const handleProductSelect = (index, prodId) => {
    const updated = [...items]
    if (prodId === '__NEW__') {
      setTargetItemIndex(index)
      setIsProductModalOpen(true)
      return
    }
    const selectedProd = products.find(p => (p.product_id || p.id) === prodId)
    updated[index].matched_product_id = prodId
    updated[index].matched_product_name = selectedProd ? (selectedProd.product_name || selectedProd.name) : ''
    updated[index].match_status = prodId ? 'MATCHED' : 'NEEDS_MATCH'
    setItems(updated)
  }

  const handleNewProductCreated = (newProd) => {
    if (targetItemIndex !== null) {
      const updated = [...items]
      updated[targetItemIndex].matched_product_id = newProd.id
      updated[targetItemIndex].matched_product_name = newProd.name
      updated[targetItemIndex].match_status = 'MATCHED'
      updated[targetItemIndex].unit_cost = newProd.purchase_price || updated[targetItemIndex].unit_cost
      setItems(updated)
    }
  }

  const removeItemRow = (index) => {
    if (items.length <= 1) return
    setItems(items.filter((_, i) => i !== index))
  }

  const grandTotal = roundVal(items.reduce((acc, item) => acc + (Number(item.quantity) * Number(item.unit_cost)), 0))

  const handleConfirmStockUpdate = async () => {
    setError(null)

    // Validation
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (!item.matched_product_id) {
        setError(`Item #${i + 1} "${item.extracted_name}" requires a matched product. Please select or create a product.`)
        return
      }
      if (Number(item.quantity) <= 0) {
        setError(`Item #${i + 1} quantity must be greater than 0.`)
        return
      }
      if (Number(item.unit_cost) < 0) {
        setError(`Item #${i + 1} unit cost cannot be negative.`)
        return
      }
    }

    try {
      setIsConfirming(true)
      const payload = {
        shop_id: 'shop_001',
        supplier_name: supplierName.trim(),
        invoice_number: invoiceNumber.trim(),
        invoice_date: invoiceDate,
        items: items.map(item => ({
          product_id: item.matched_product_id,
          quantity: Number(item.quantity),
          unit_cost: Number(item.unit_cost)
        }))
      }

      const res = await fetchWithAuth('/api/purchases/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to confirm stock update')
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
          <ArrowLeft size={16} /> Re-upload / Back
        </button>

        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.8rem', background: extractionData.mode === 'ai' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(245, 158, 11, 0.15)', color: extractionData.mode === 'ai' ? 'var(--accent-blue)' : 'var(--accent-amber)', border: `1px solid ${extractionData.mode === 'ai' ? 'var(--accent-blue)' : 'var(--accent-amber)'}` }}>
          <Cpu size={14} /> Extraction Mode: {extractionData.mode === 'ai' ? 'Vision AI' : 'Demo Fallback'}
        </div>
      </div>

      {/* Duplicate Warning Banner */}
      {extractionData.duplicate_warning && (
        <div style={{ background: 'rgba(245, 158, 11, 0.15)', border: '1px solid var(--accent-amber)', color: 'var(--accent-amber)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={18} />
          <span style={{ fontSize: '0.9rem', fontWeight: '500' }}>{extractionData.duplicate_warning}</span>
        </div>
      )}

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* Invoice Header Details */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', fontWeight: '600' }}>Invoice Details Review</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Supplier Name</label>
            <input
              type="text"
              value={supplierName}
              onChange={e => setSupplierName(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Invoice Number</label>
            <input
              type="text"
              value={invoiceNumber}
              onChange={e => setInvoiceNumber(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Invoice Date</label>
            <input
              type="date"
              value={invoiceDate}
              onChange={e => setInvoiceDate(e.target.value)}
              style={{ width: '100%', padding: '0.5rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
            />
          </div>
        </div>
      </div>

      {/* Extracted Line Items Review Table */}
      <div className="card" style={{ padding: 0, overflowX: 'auto', marginBottom: '1.5rem' }}>
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: '600' }}>Line Items ({items.length})</h4>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Check matching status before confirming</span>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
          <thead>
            <tr style={{ background: '#0f172a', color: 'var(--text-muted)', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Extracted Item</th>
              <th style={{ padding: '0.75rem 1rem' }}>Match Status</th>
              <th style={{ padding: '0.75rem 1rem' }}>Map to Product</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Qty</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Cost (₹)</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Total (₹)</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid var(--border-color)' }}>
                <td style={{ padding: '0.75rem 1rem', fontWeight: '500' }}>
                  {item.extracted_name}
                  {item.confidence !== undefined && (
                    <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      <span style={{ padding: '0.15rem 0.4rem', borderRadius: '0.25rem', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-blue)', fontWeight: '600', border: '1px solid rgba(59,130,246,0.2)' }}>
                        AI Confidence: {Math.round((item.confidence || 0) * 100)}%
                      </span>
                    </span>
                  )}
                </td>

                <td style={{ padding: '0.75rem 1rem' }}>
                  {item.match_status === 'MATCHED' ? (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', fontWeight: '600' }}>
                      <CheckCircle size={12} /> Matched
                    </span>
                  ) : (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', padding: '0.2rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontWeight: '600' }}>
                      <AlertTriangle size={12} /> Needs Match
                    </span>
                  )}
                </td>

                <td style={{ padding: '0.75rem 1rem' }}>
                  <select
                    value={item.matched_product_id || ''}
                    onChange={e => handleProductSelect(idx, e.target.value)}
                    style={{ width: '100%', padding: '0.4rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white', fontSize: '0.85rem' }}
                  >
                    <option value="">-- Select Product --</option>
                    {products.map(p => (
                      <option key={p.product_id || p.id} value={p.product_id || p.id}>
                        {p.product_name || p.name}
                      </option>
                    ))}
                    <option value="__NEW__" style={{ color: 'var(--accent-blue)', fontWeight: 'bold' }}>+ Create New Product</option>
                  </select>
                </td>

                <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                  <input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={e => handleItemChange(idx, 'quantity', e.target.value)}
                    style={{ width: '70px', padding: '0.35rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white', textAlign: 'right' }}
                  />
                </td>

                <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={item.unit_cost}
                    onChange={e => handleItemChange(idx, 'unit_cost', e.target.value)}
                    style={{ width: '85px', padding: '0.35rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white', textAlign: 'right' }}
                  />
                </td>

                <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontWeight: '600', color: 'var(--accent-green)' }}>
                  ₹{(Number(item.quantity) * Number(item.unit_cost)).toFixed(2)}
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
            ))}
          </tbody>
        </table>
      </div>

      {/* Grand Total & Confirmation Action Footer */}
      <div className="card" style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
        <div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block' }}>Calculated Total Amount</span>
          <span style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--accent-green)' }}>₹{grandTotal.toFixed(2)}</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.4rem' }}>
          <button
            onClick={handleConfirmStockUpdate}
            disabled={isConfirming}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem', background: 'var(--accent-green)', border: 'none', color: 'white', borderRadius: '0.5rem', fontWeight: '600', fontSize: '1rem', cursor: 'pointer' }}
          >
            <ShieldCheck size={20} /> {isConfirming ? 'Updating Inventory...' : 'Confirm Stock Update'}
          </button>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            ⚠️ Inventory is ONLY updated after clicking Confirm Stock Update
          </span>
        </div>
      </div>

      {/* New Product Modal for Unmatched Products */}
      <ProductFormModal
        isOpen={isProductModalOpen}
        onClose={() => setIsProductModalOpen(false)}
        onSave={handleNewProductCreated}
        initialData={targetItemIndex !== null ? {
          name: items[targetItemIndex]?.extracted_name || '',
          purchase_price: items[targetItemIndex]?.unit_cost || 0
        } : null}
      />
    </div>
  )
}
