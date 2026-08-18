import React, { useState, useEffect } from 'react'
import { Plus, ShoppingCart, Search, Edit3, PackageCheck, AlertTriangle, AlertCircle } from 'lucide-react'
import ProductFormModal from './ProductFormModal'
import PurchaseFormModal from './PurchaseFormModal'

export default function InventoryView({ onInventoryChange }) {
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('ALL')
  const [feedback, setFeedback] = useState(null)

  // Modals state
  const [isProductModalOpen, setIsProductModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [isPurchaseModalOpen, setIsPurchaseModalOpen] = useState(false)

  const fetchInventory = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/inventory')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setInventory(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchInventory()
  }, [])

  const handleProductSave = (product) => {
    setFeedback(`Product "${product.name}" saved successfully.`)
    fetchInventory()
    if (onInventoryChange) onInventoryChange()
    setTimeout(() => setFeedback(null), 4000)
  }

  const handlePurchaseSuccess = (res) => {
    setFeedback(`Purchase confirmed! ${res.updated_inventories?.length || 0} inventory items updated.`)
    fetchInventory()
    if (onInventoryChange) onInventoryChange()
    setTimeout(() => setFeedback(null), 4000)
  }

  const categories = ['ALL', ...Array.from(new Set(inventory.map(item => item.category)))]

  const filteredInventory = inventory.filter(item => {
    const matchesSearch = item.product_name.toLowerCase().includes(search.toLowerCase()) ||
                          (item.brand && item.brand.toLowerCase().includes(search.toLowerCase()))
    const matchesCategory = selectedCategory === 'ALL' || item.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  // Summary Metrics
  const totalProducts = inventory.length
  const totalValue = inventory.reduce((acc, curr) => acc + curr.inventory_value, 0)
  const lowStockCount = inventory.filter(i => i.stock_status === 'LOW_STOCK').length
  const outOfStockCount = inventory.filter(i => i.stock_status === 'OUT_OF_STOCK').length

  const getStatusBadge = (status) => {
    if (status === 'OUT_OF_STOCK') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', fontWeight: '600', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-red)', border: '1px solid var(--accent-red)' }}>
          <AlertCircle size={12} /> OUT OF STOCK
        </span>
      )
    }
    if (status === 'LOW_STOCK') {
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', fontWeight: '600', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', border: '1px solid var(--accent-amber)' }}>
          <AlertTriangle size={12} /> LOW STOCK
        </span>
      )
    }
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', borderRadius: '0.375rem', fontSize: '0.75rem', fontWeight: '600', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-green)', border: '1px solid var(--accent-green)' }}>
        <PackageCheck size={12} /> HEALTHY
      </span>
    )
  }

  return (
    <div>
      {/* Metric Summary Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ padding: '1rem', marginBottom: 0 }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Products</p>
          <p style={{ fontSize: '1.4rem', fontWeight: '700' }}>{totalProducts}</p>
        </div>
        <div className="card" style={{ padding: '1rem', marginBottom: 0 }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Inventory Valuation</p>
          <p style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-green)' }}>₹{totalValue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
        </div>
        <div className="card" style={{ padding: '1rem', marginBottom: 0 }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Low Stock Items</p>
          <p style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-amber)' }}>{lowStockCount}</p>
        </div>
        <div className="card" style={{ padding: '1rem', marginBottom: 0 }}>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Out of Stock</p>
          <p style={{ fontSize: '1.4rem', fontWeight: '700', color: 'var(--accent-red)' }}>{outOfStockCount}</p>
        </div>
      </div>

      {feedback && (
        <div className="status-box" style={{ width: '100%', marginBottom: '1rem' }}>
          <PackageCheck size={16} /> {feedback}
        </div>
      )}

      {/* Action Controls & Filters */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '0.75rem', flex: 1, minWidth: '280px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search products..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ width: '100%', padding: '0.5rem 0.75rem 0.5rem 2.25rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
              />
            </div>
            <select
              value={selectedCategory}
              onChange={e => setSelectedCategory(e.target.value)}
              style={{ padding: '0.5rem 0.75rem', background: '#0f172a', border: '1px solid var(--border-color)', borderRadius: '0.375rem', color: 'white' }}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setIsPurchaseModalOpen(true)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.5rem 0.9rem', background: 'var(--bg-card)', border: '1px solid var(--accent-green)', color: 'var(--accent-green)', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '500' }}
            >
              <ShoppingCart size={16} /> Record Purchase
            </button>
            <button
              onClick={() => { setEditingProduct(null); setIsProductModalOpen(true); }}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.5rem 0.9rem', background: 'var(--accent-blue)', border: 'none', color: 'white', borderRadius: '0.375rem', cursor: 'pointer', fontWeight: '500' }}
            >
              <Plus size={16} /> Add Product
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading inventory...</div>
      ) : error ? (
        <div style={{ color: 'var(--accent-red)', padding: '1rem' }}>Failed to load inventory: {error}</div>
      ) : (
        <>
          {/* Desktop Table View */}
          <div className="desktop-only card" style={{ overflowX: 'auto', padding: 0 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ background: '#0f172a', borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>Product</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Category</th>
                  <th style={{ padding: '0.75rem 1rem' }}>Stock Status</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Qty</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Cost</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Price</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Inventory Value</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredInventory.map(item => (
                  <tr key={item.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: '500' }}>
                      {item.product_name}
                      {item.brand && <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.brand}</span>}
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-muted)' }}>{item.category}</td>
                    <td style={{ padding: '0.75rem 1rem' }}>{getStatusBadge(item.stock_status)}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontWeight: '600' }}>{item.quantity} {item.unit}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>₹{item.purchase_price.toFixed(2)}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>₹{item.selling_price.toFixed(2)}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'right', color: 'var(--accent-green)', fontWeight: '600' }}>₹{item.inventory_value.toFixed(2)}</td>
                    <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                      <button
                        onClick={() => { setEditingProduct(item); setIsProductModalOpen(true); }}
                        style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer' }}
                        title="Edit Product"
                      >
                        <Edit3 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Product Cards View */}
          <div className="mobile-only" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {filteredInventory.map(item => (
              <div key={item.id} className="card" style={{ padding: '1rem', marginBottom: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: '600' }}>{item.product_name}</h4>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{item.category} • {item.brand || 'No brand'}</p>
                  </div>
                  <button
                    onClick={() => { setEditingProduct(item); setIsProductModalOpen(true); }}
                    style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer' }}
                  >
                    <Edit3 size={18} />
                  </button>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
                  <div>{getStatusBadge(item.stock_status)}</div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: '700' }}>{item.quantity} {item.unit}</span>
                    <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--accent-green)' }}>Val: ₹{item.inventory_value.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Modals */}
      <ProductFormModal
        isOpen={isProductModalOpen}
        onClose={() => setIsProductModalOpen(false)}
        onSave={handleProductSave}
        initialData={editingProduct}
      />

      <PurchaseFormModal
        isOpen={isPurchaseModalOpen}
        onClose={() => setIsPurchaseModalOpen(false)}
        onPurchaseSuccess={handlePurchaseSuccess}
        products={inventory}
      />
    </div>
  )
}
