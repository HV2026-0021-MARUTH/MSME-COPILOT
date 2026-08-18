import { fetchWithAuth } from '../lib/api';
import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'

export default function ProductFormModal({ isOpen, onClose, onSave, initialData }) {
  const [formData, setFormData] = useState({
    name: '',
    category: 'General',
    brand: '',
    unit: 'pack',
    purchase_price: 0,
    selling_price: 0,
    reorder_level: 10
  })
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        category: initialData.category || 'General',
        brand: initialData.brand || '',
        unit: initialData.unit || 'pack',
        purchase_price: initialData.purchase_price ?? 0,
        selling_price: initialData.selling_price ?? 0,
        reorder_level: initialData.reorder_level ?? 10
      })
    } else {
      setFormData({
        name: '',
        category: 'General',
        brand: '',
        unit: 'pack',
        purchase_price: 0,
        selling_price: 0,
        reorder_level: 10
      })
    }
    setError(null)
  }, [initialData, isOpen])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!formData.name.trim()) {
      setError('Product name is required.')
      return
    }
    if (Number(formData.purchase_price) < 0) {
      setError('Purchase price cannot be negative.')
      return
    }
    if (Number(formData.selling_price) <= 0) {
      setError('Selling price must be explicitly entered and greater than 0.')
      return
    }
    if (Number(formData.selling_price) < Number(formData.purchase_price)) {
      setError('Selling price cannot be less than purchase cost.')
      return
    }
    if (Number(formData.reorder_level) < 0) {
      setError('Reorder level cannot be negative.')
      return
    }

    try {
      setIsSubmitting(true)
      const url = initialData ? `/api/products/${initialData.product_id || initialData.id}` : '/api/products'
      const method = initialData ? 'PUT' : 'POST'

      const payload = {
        name: formData.name.trim(),
        category: formData.category.trim() || 'General',
        brand: formData.brand.trim() || null,
        unit: formData.unit.trim() || 'pack',
        purchase_price: Number(formData.purchase_price),
        selling_price: Number(formData.selling_price),
        reorder_level: Number(formData.reorder_level)
      }

      const res = await fetchWithAuth(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to save product')
      }

      const savedProduct = await res.json()
      onSave(savedProduct)
      onClose()
    } catch (err) {
      setError(err.message)
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
        width: '100%', maxWidth: '500px',
        padding: '1.5rem', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: '600' }}>
            {initialData ? 'Edit Product' : 'Add New Product'}
          </h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {error && (
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.5rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Product Name *</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
              placeholder="e.g. Coca-Cola 250ml"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Category</label>
              <input
                type="text"
                value={formData.category}
                onChange={e => setFormData({ ...formData, category: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                placeholder="e.g. Beverages"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Brand</label>
              <input
                type="text"
                value={formData.brand}
                onChange={e => setFormData({ ...formData, brand: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                placeholder="e.g. Coca-Cola"
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Unit</label>
              <input
                type="text"
                value={formData.unit}
                onChange={e => setFormData({ ...formData, unit: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
                placeholder="pack / bottle"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Cost (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.purchase_price}
                onChange={e => setFormData({ ...formData, purchase_price: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Selling Price (₹) *</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={formData.selling_price}
                onChange={e => setFormData({ ...formData, selling_price: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Reorder Level</label>
            <input
              type="number"
              min="0"
              value={formData.reorder_level}
              onChange={e => setFormData({ ...formData, reorder_level: e.target.value })}
              style={{ width: '100%', padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
            />
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
              style={{ padding: '0.5rem 1rem', background: 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '500' }}
            >
              {isSubmitting ? 'Saving...' : (initialData ? 'Update Product' : 'Create Product')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
