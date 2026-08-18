import { fetchWithAuth } from '../lib/api';
import React, { useState } from 'react'
import { UploadCloud, AlertCircle, CheckCircle2, FileText, Loader2, ArrowRight } from 'lucide-react'

export default function BulkImportView({ onImportComplete }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [previewData, setPreviewData] = useState(null)
  const [importSummary, setImportSummary] = useState(null)
  
  const [createNewProducts, setCreateNewProducts] = useState(false)

  const handleFileUpload = async (selectedFile) => {
    if (!selectedFile) return
    setFile(selectedFile)
    setError(null)
    setPreviewData(null)
    setImportSummary(null)
    
    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      setLoading(true)
      const res = await fetchWithAuth('/api/import/preview', {
        method: 'POST',
        body: formData
      })
      
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to preview file')
      }
      
      setPreviewData(data)
    } catch (err) {
      setError('Unable to complete this action. MARUTHI backend is unavailable.')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmImport = async () => {
    if (!previewData) return
    
    try {
      setLoading(true)
      setError(null)
      
      const newProductsInfo = previewData.new_products.map(name => ({
        name,
        category: "Uncategorized",
        selling_price: 0.0,
        purchase_price: 0.0,
        unit: "unit"
      }))
      
      const payload = {
        shop_id: "shop_001",
        file_id: previewData.file_id,
        mapping: previewData.mapped_columns,
        create_new_products: createNewProducts,
        new_products_info: newProductsInfo
      }
      
      const res = await fetchWithAuth('/api/import/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
      
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Import failed')
      }
      
      setImportSummary(data)
      setPreviewData(null)
      if (onImportComplete) {
        onImportComplete()
      }
    } catch (err) {
      setError('Unable to complete this action. MARUTHI backend is unavailable.')
    } finally {
      setLoading(false)
    }
  }

  if (importSummary) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <CheckCircle2 size={48} style={{ color: 'var(--accent-green)', margin: '0 auto 1rem' }} />
        <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '1rem' }}>Import Complete</h2>
        <div style={{ background: 'var(--bg-default)', padding: '1.5rem', borderRadius: '0.5rem', textAlign: 'left', display: 'inline-block', minWidth: '300px' }}>
          <p style={{ margin: '0.5rem 0' }}><strong>Imported Sales:</strong> {importSummary.imported_sales}</p>
          <p style={{ margin: '0.5rem 0' }}><strong>Products Created:</strong> {importSummary.products_created}</p>
          <p style={{ margin: '0.5rem 0' }}><strong>Skipped Rows (Invalid):</strong> {importSummary.skipped_rows}</p>
          <p style={{ margin: '0.5rem 0' }}><strong>Errors:</strong> {importSummary.errors}</p>
          <p style={{ margin: '0.5rem 0' }}><strong>Duplicates Skipped:</strong> {importSummary.duplicates_detected}</p>
        </div>
        <div style={{ marginTop: '2rem' }}>
          <button 
            onClick={() => { setImportSummary(null); setFile(null); }}
            style={{ padding: '0.75rem 1.5rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '0.5rem', fontWeight: '600', cursor: 'pointer' }}
          >
            Import Another File
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card" style={{ padding: '2rem 1.5rem', textAlign: 'center' }}>
      <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.15)', border: '1px solid var(--accent-blue)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}>
        <FileText size={32} style={{ color: 'var(--accent-blue)' }} />
      </div>

      <h2 style={{ fontSize: '1.4rem', fontWeight: '700', marginBottom: '0.5rem' }}>Bulk CSV/Excel Import</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '500px', margin: '0 auto 1.5rem' }}>
        Upload historical sales data. Supported formats: .csv, .xlsx
      </p>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '0.75rem 1rem', borderRadius: '0.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', textAlign: 'left' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {!previewData && !loading && (
        <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1.5rem', background: 'var(--accent-blue)', color: 'white', borderRadius: '0.5rem', fontWeight: '600', cursor: 'pointer' }}>
          <UploadCloud size={20} /> Select File
          <input
            type="file"
            accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
            onChange={e => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
            style={{ display: 'none' }}
          />
        </label>
      )}

      {loading && (
        <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
          <Loader2 size={36} className="spin" style={{ color: 'var(--accent-blue)' }} />
          <p style={{ fontWeight: '500', color: 'var(--text-main)' }}>Processing...</p>
        </div>
      )}

      {previewData && !loading && (
        <div style={{ textAlign: 'left', marginTop: '1.5rem', background: 'var(--bg-default)', padding: '1.5rem', borderRadius: '0.5rem' }}>
          <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Data Preview</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div><strong>Total Rows:</strong> {previewData.total_rows}</div>
            <div style={{ color: 'var(--accent-green)' }}><strong>Valid Rows:</strong> {previewData.valid_rows}</div>
            <div style={{ color: 'var(--accent-red)' }}><strong>Invalid Rows:</strong> {previewData.invalid_rows}</div>
          </div>

          <h4 style={{ marginBottom: '0.5rem' }}>Column Mapping</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            <div>Date ➔ {previewData.mapped_columns.date_col || 'Missing'}</div>
            <div>Product ➔ {previewData.mapped_columns.product_col || 'Missing'}</div>
            <div>Quantity ➔ {previewData.mapped_columns.quantity_col || 'Missing'}</div>
            <div>Selling Price ➔ {previewData.mapped_columns.selling_price_col || 'Missing'}</div>
            <div>Cost Price ➔ {previewData.mapped_columns.cost_price_col || 'None'}</div>
          </div>

          {previewData.new_products.length > 0 && (
            <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid var(--accent-amber)', padding: '1rem', borderRadius: '0.5rem', marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-amber)', marginBottom: '0.5rem', fontWeight: '600' }}>
                <AlertCircle size={18} />
                {previewData.new_products.length} New Products Detected
              </div>
              <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                These products do not currently exist in your product catalog. Would you like to create them before importing the sales records?
              </p>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={createNewProducts} 
                  onChange={e => setCreateNewProducts(e.target.checked)} 
                />
                Create missing products automatically
              </label>
            </div>
          )}
          
          {previewData.invalid_rows > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ marginBottom: '0.5rem', color: 'var(--accent-red)' }}>Sample Errors:</h4>
              <ul style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                {previewData.rows.filter(r => !r.is_valid).slice(0, 5).map(r => (
                  <li key={r.row_index}>Row {r.row_index + 1}: {r.errors.join(', ')}</li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
            <button 
              onClick={() => { setPreviewData(null); setFile(null); }}
              style={{ padding: '0.6rem 1.2rem', background: 'transparent', color: 'var(--text-main)', border: '1px solid var(--border-color)', borderRadius: '0.5rem', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button 
              onClick={handleConfirmImport}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.5rem', background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '0.5rem', fontWeight: '600', cursor: 'pointer' }}
            >
              Confirm Import <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
