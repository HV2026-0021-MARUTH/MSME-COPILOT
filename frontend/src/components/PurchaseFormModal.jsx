import { fetchWithAuth } from '../lib/api';
import React, { useState } from 'react'
import { X, Plus, Trash2 } from 'lucide-react'

export default function PurchaseFormModal({ isOpen, onClose, onPurchaseSuccess, products }) {
  const [supplierName, setSupplierName] = useState('')
  const [invoiceNumber, setInvoiceNumber] = useState('')
  const [items, setItems] = useState([
    { product_id: products[0]?.product_id || products[0]?.id || '', quantity: 10, unit_cost: products[0]?.purchase_price || 0 }
  ])
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleItemChange = (index, field, value) => {
    const updated = [...items]
    updated[index][field] = value

    if (field === 'product_id') {
      const selectedProd = products.find(p => (p.product_id || p.id) === value)
      if (selectedProd) {
        updated[index].unit_cost = selectedProd.purchase_price
      }
    }
    setItems(updated)
  }

  const addItemRow = () => {
    setItems([
      ...items,
      { product_id: products[0]?.product_id || products[0]?.id || '', quantity: 10, unit_cost: products[0]?.purchase_price || 0 }
    ])
  }

  const removeItemRow = (index) => {
    if (items.length <= 1) return
    setItems(items.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (items.length === 0) {
      setError('Please add at least one item.')
      return
    }

    for (const item of items) {
      if (!item.product_id) {
        setError('Please select a valid product.')
        return
      }
      if (Number(item.quantity) <= 0) {
        setError('Quantity must be greater than 0.')
        return
      }
      if (Number(item.unit_cost) < 0) {
        setError('Unit cost cannot be negative.')
        return
      }
    }

    try {
      setIsSubmitting(true)
      const payload = {
        shop_id: 'shop_001',
        supplier_name: supplierName.trim() || 'Manual Purchase',
        invoice_number: invoiceNumber.trim() || null,
        items: items.map(i => ({
          product_id: i.product_id,
          quantity: Number(i.quantity),
          unit_cost: Number(i.unit_cost)
        }))
      }

      const res = await fetchWithAuth('/api/purchases/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Purchase recording failed')
      }

      const result = await res.json()
      onPurchaseSuccess(result)
      onClose()
    } catch (err) {
      setError('Unable to complete this action. MARUTHI backend is unavailable.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.8)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '1rem'
    }}>
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '0.75rem',
        width: '100%', maxWidth: '600px',
        padding: '1.5rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: '600' }}>Record Manual Purchase</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.5rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Supplier Name</label>
              <input
                type="text"
                value={supplierName}
                onChange={e => setSupplierName(e.target.value)}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                placeholder="e.g. Wholesale Depot"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Invoice No. (Optional)</label>
              <input
                type="text"
                value={invoiceNumber}
                onChange={e => setInvoiceNumber(e.target.value)}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                placeholder="e.g. INV-9081"
              />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: '500', color: 'var(--text-main)' }}>Purchase Items</label>
              <button
                type="button"
                onClick={addItemRow}
                style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem', cursor: 'pointer', fontSize: '0.85rem' }}
              >
                <Plus size={14} /> Add Item
              </button>
            </div>

            {items.map((item, idx) => (
              <div key={idx} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 40px', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                <select
                  value={item.product_id}
                  onChange={e => handleItemChange(idx, 'product_id', e.target.value)}
                  style={{ padding: '0.5rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                >
                  {products.map(p => (
                    <option key={p.product_id || p.id} value={p.product_id || p.id}>
                      {p.product_name || p.name}
                    </option>
                  ))}
                </select>

                <input
                  type="number"
                  min="1"
                  placeholder="Qty"
                  value={item.quantity}
                  onChange={e => handleItemChange(idx, 'quantity', e.target.value)}
                  style={{ padding: '0.5rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                />

                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Cost ₹"
                  value={item.unit_cost}
                  onChange={e => handleItemChange(idx, 'unit_cost', e.target.value)}
                  style={{ padding: '0.5rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                />

                <button
                  type="button"
                  onClick={() => removeItemRow(idx)}
                  disabled={items.length <= 1}
                  style={{ background: 'none', border: 'none', color: items.length <= 1 ? 'var(--border-color)' : 'var(--accent-red)', cursor: items.length <= 1 ? 'default' : 'pointer' }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              onClick={onClose}
              style={{ padding: '0.5rem 1rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-muted)', borderRadius: '0.375rem', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              style={{ padding: '0.5rem 1rem', background: 'var(--accent-green)', border: 'none', color: 'white', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '500' }}
            >
              {isSubmitting ? 'Recording...' : 'Confirm Purchase'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
