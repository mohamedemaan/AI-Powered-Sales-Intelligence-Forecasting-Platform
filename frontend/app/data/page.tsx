'use client'

import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { useAuth } from '../../hooks/useAuth'
import api from '../../lib/api'
import {
  UploadCloud,
  FileText,
  Calendar,
  Layers,
  ShoppingBag,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Trash2,
  Table
} from 'lucide-react'

export default function DataManagementPage() {
  const queryClient = useQueryClient()
  const { activeOrg } = useAuth()
  const isViewer = activeOrg?.role === 'VIEWER' || activeOrg?.role === 'MEMBER'
  const isOwnerOrAdmin = activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN'

  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [statusData, setStatusData] = useState<{ total_raw_records: number } | null>(null)
  const [previewData, setPreviewData] = useState<any>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [replaceExisting, setReplaceExisting] = useState(true)
  const [deduplicating, setDeduplicating] = useState(false)
  const [dedupResult, setDedupResult] = useState<any>(null)
  const [resetting, setResetting] = useState(false)
  const [resetResult, setResetResult] = useState<any>(null)
  const [isDragging, setIsDragging] = useState(false)

  const fetchStatus = async () => {
    try {
      const res = await api.get('/api/v1/data/status')
      setStatusData(res.data)
    } catch (err: any) {
      console.error('Failed to fetch data status', err)
    }
  }

  const fetchPreview = async () => {
    setLoadingPreview(true)
    try {
      const res = await api.get('/api/v1/data/preview?limit=10')
      setPreviewData(res.data)
    } catch (err: any) {
      console.error('Failed to fetch dataset preview', err)
    } finally {
      setLoadingPreview(false)
    }
  }

  const handleDeduplicate = async () => {
    setDeduplicating(true)
    setErrorMsg(null)
    setDedupResult(null)
    setResetResult(null)
    try {
      const res = await api.post('/api/v1/data/clean-duplicates')
      setDedupResult(res.data)
      fetchStatus()
      fetchPreview()
      queryClient.invalidateQueries()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to remove duplicates.')
    } finally {
      setDeduplicating(false)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to completely clear all sales records and forecasts? This will return the dashboard to a clean initial state.')) {
      return
    }
    setResetting(true)
    setErrorMsg(null)
    setUploadResult(null)
    setDedupResult(null)
    setResetResult(null)
    try {
      const res = await api.post('/api/v1/data/reset')
      setResetResult(res.data)
      fetchStatus()
      fetchPreview()
      queryClient.invalidateQueries()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to reset sales data.')
    } finally {
      setResetting(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    fetchPreview()
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const selected = e.target.files[0]
      setFile(selected)
      setErrorMsg(null)
      setUploadResult(null)
      setDedupResult(null)
      setResetResult(null)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setErrorMsg('Please select a CSV file first.')
      return
    }

    if (!file.name.endsWith('.csv')) {
      setErrorMsg('Only .csv files are supported.')
      return
    }

    setUploading(true)
    setErrorMsg(null)
    setUploadResult(null)
    setDedupResult(null)
    setResetResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post(`/api/v1/data/upload?replace=${replaceExisting}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setUploadResult(res.data)
      setFile(null)
      fetchStatus()
      fetchPreview()
      // Invalidate all React Query caches across the app
      queryClient.invalidateQueries()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload and process dataset.')
    } finally {
      setUploading(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile)
        setErrorMsg(null)
        setUploadResult(null)
        setDedupResult(null)
        setResetResult(null)
      } else {
        setErrorMsg('Only .csv files are supported.')
      }
    }
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Data Management & Ingestion</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Upload sales CSV datasets, inspect schema columns, verify date spans, and audit data hygiene.
          </p>
        </div>
        <Link
          href="/cleaning"
          className="inline-flex items-center gap-2 bg-primary/20 text-primary border border-primary/40 hover:bg-primary/30 text-xs px-3.5 py-2 rounded-lg font-semibold transition shrink-0"
        >
          Open Data Cleaning Studio &rarr;
        </Link>
      </header>

      {/* RBAC Viewer Warning Banner */}
      {isViewer && (
        <div className="p-4 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>View-Only Workspace Access ({activeOrg?.role}):</strong> You have read-only permissions for this workspace. Uploading datasets, deduplication, and resetting data require an Analyst, Admin, or Owner role.
          </span>
        </div>
      )}

      {/* Dataset Status Banner */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div>
          <span className="text-xs text-slate-400 font-medium uppercase tracking-wider block">
            Active Historical Sales Ledger
          </span>
          <span className="text-3xl font-bold text-white mt-0.5 block">
            {statusData ? `${statusData.total_raw_records.toLocaleString()} Transactions` : 'Loading...'}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button 
            onClick={() => { fetchStatus(); fetchPreview(); }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Status
          </button>
          <button
            onClick={handleDeduplicate}
            disabled={deduplicating || !statusData || statusData.total_raw_records === 0 || isViewer}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-500/40 rounded-lg hover:bg-amber-500/30 transition disabled:opacity-50"
            title={isViewer ? "Deduplication disabled for View-only role" : "Clean duplicate records created by repeated uploads"}
          >
            {deduplicating ? 'Cleaning...' : 'Deduplicate'}
          </button>
          <button
            onClick={handleReset}
            disabled={resetting || !statusData || statusData.total_raw_records === 0 || !isOwnerOrAdmin}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-danger/20 text-danger border border-danger/40 rounded-lg hover:bg-danger/30 transition disabled:opacity-50"
            title={!isOwnerOrAdmin ? "Clear data restricted to Owner or Admin" : "Wipe database to return to initial empty state"}
          >
            <Trash2 className="w-3.5 h-3.5" /> {resetting ? 'Clearing...' : 'Clear All Data'}
          </button>
        </div>
      </div>

      {dedupResult && (
        <div className="p-4 bg-amber-500/10 border border-amber-500/40 text-amber-200 rounded-lg text-sm flex items-center justify-between">
          <span>
            Deduplication complete: Removed <strong>{dedupResult.records_removed.toLocaleString()}</strong> duplicate rows. Retained <strong>{dedupResult.total_records.toLocaleString()}</strong> unique transactions.
          </span>
          <button onClick={() => setDedupResult(null)} className="text-xs text-slate-400 hover:text-white">Dismiss</button>
        </div>
      )}

      {resetResult && (
        <div className="p-4 bg-danger/10 border border-danger/40 text-danger rounded-lg text-sm flex items-center justify-between">
          <span>
            Database reset complete: Successfully cleared <strong>{resetResult.records_cleared.toLocaleString()}</strong> records. The dashboard is now in its clean initial state.
          </span>
          <button onClick={() => setResetResult(null)} className="text-xs text-slate-400 hover:text-white">Dismiss</button>
        </div>
      )}

      {/* CSV Upload Card */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-white">Upload New Sales Dataset</h3>
          <span className="text-xs text-emerald-400 font-medium bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            Schema Auto-Detection Active
          </span>
        </div>

        <p className="text-xs text-slate-300">
          Upload any sales CSV dataset. Common retail schemas (including <strong className="text-white">Sample Superstore</strong>, Kaggle retail, and Shopify exports) are automatically recognized and mapped:
        </p>
        <div className="flex flex-wrap gap-2 text-[11px] font-mono text-slate-300 pb-1">
          <span className="bg-slate-800/80 px-2 py-1 rounded border border-slate-700">Order Date &rarr; date</span>
          <span className="bg-slate-800/80 px-2 py-1 rounded border border-slate-700">Product ID / SKU &rarr; sku</span>
          <span className="bg-slate-800/80 px-2 py-1 rounded border border-slate-700">Quantity &rarr; units_sold</span>
          <span className="bg-slate-800/80 px-2 py-1 rounded border border-slate-700">Sales &rarr; total_sales / price</span>
          <span className="bg-slate-800/80 px-2 py-1 rounded border border-slate-700">Profit &rarr; profit</span>
        </div>

        <form onSubmit={handleUpload} className="space-y-4">
          <div 
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition ${
              isDragging ? 'border-primary bg-primary/10' : 'border-slate-700 hover:border-primary/60'
            }`}
          >
            <input 
              type="file" 
              accept=".csv"
              onChange={handleFileChange}
              className="block w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-white hover:file:bg-blue-600 cursor-pointer"
            />
            {file ? (
              <p className="mt-3 text-xs text-emerald-400 font-medium">Selected file: {file.name} ({(file.size / 1024).toFixed(1)} KB)</p>
            ) : (
              <p className="mt-2 text-xs text-slate-500">or drag and drop your CSV file directly into this dropzone</p>
            )}
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="replaceExisting"
              checked={replaceExisting}
              onChange={(e) => setReplaceExisting(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-primary focus:ring-0 cursor-pointer"
            />
            <label htmlFor="replaceExisting" className="text-xs text-slate-300 cursor-pointer select-none">
              Replace existing records with this upload <span className="text-slate-400">(recommended to prevent duplicate data accumulation)</span>
            </label>
          </div>

          {errorMsg && (
            <div className="p-3 bg-danger/20 border border-danger/50 text-danger rounded-lg text-xs">
              {errorMsg}
            </div>
          )}

          {uploadResult && (
            <div className="p-3 bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 rounded-lg text-xs">
              Successfully processed and ingested {uploadResult.records_processed.toLocaleString()} sales records into the database!
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={uploading || !file || isViewer}
              className="bg-primary text-white text-xs px-5 py-2 rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50 transition"
              title={isViewer ? "Uploading disabled for View-only role" : undefined}
            >
              {uploading ? 'Processing Dataset...' : 'Upload & Ingest'}
            </button>
          </div>
        </form>
      </div>

      {/* Dataset Preview Section (Module 7) */}
      {previewData?.has_data && (
        <div className="bg-surface p-6 rounded-xl border border-slate-700 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <Table className="w-4 h-4 text-primary" /> Active Dataset Telemetry & Preview
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Source: <span className="font-mono text-slate-200">{previewData.filename}</span>
              </p>
            </div>
            <Link
              href="/analytics"
              className="inline-flex items-center gap-1.5 text-xs text-primary font-semibold hover:underline"
            >
              Open in Sales Analytics <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Metadata Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[11px] text-slate-400 block">Total Rows</span>
              <span className="text-lg font-bold text-white mt-0.5 block">{previewData.row_count.toLocaleString()}</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[11px] text-slate-400 block">Columns</span>
              <span className="text-lg font-bold text-white mt-0.5 block">{previewData.column_count}</span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[11px] text-slate-400 block">Date Span</span>
              <span className="text-lg font-bold text-white mt-0.5 block">
                {previewData.date_coverage?.span_days ? `${previewData.date_coverage.span_days} days` : 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[11px] text-slate-400 block">Earliest Date</span>
              <span className="text-xs font-mono font-medium text-slate-200 mt-1 block">
                {previewData.date_coverage?.min_date || 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[11px] text-slate-400 block">Latest Date</span>
              <span className="text-xs font-mono font-medium text-slate-200 mt-1 block">
                {previewData.date_coverage?.max_date || 'N/A'}
              </span>
            </div>
            <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[11px] text-slate-400 block">Catalog Scope</span>
              <span className="text-xs font-medium text-slate-200 mt-1 block">
                {previewData.product_count} SKUs / {previewData.category_count} Cats
              </span>
            </div>
          </div>

          {/* Missing Values Audit */}
          <div className="bg-slate-900/40 p-4 rounded-lg border border-slate-800">
            <h4 className="text-xs font-semibold text-slate-300 mb-2">Schema Quality & Missing Value Audit</h4>
            <div className="flex flex-wrap gap-2 text-[11px]">
              <span className={`px-2 py-0.5 rounded border ${
                previewData.missing_values?.order_id === 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border-amber-500/20'
              }`}>
                Order IDs Missing: {previewData.missing_values?.order_id?.toLocaleString() || 0}
              </span>
              <span className={`px-2 py-0.5 rounded border ${
                previewData.missing_values?.category === 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                Category Nulls: {previewData.missing_values?.category?.toLocaleString() || 0}
              </span>
              <span className={`px-2 py-0.5 rounded border ${
                previewData.missing_values?.profit === 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                Profit Nulls: {previewData.missing_values?.profit?.toLocaleString() || 0}
              </span>
              <span className={`px-2 py-0.5 rounded border ${
                previewData.missing_values?.price === 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}>
                Price Nulls: {previewData.missing_values?.price?.toLocaleString() || 0}
              </span>
            </div>
          </div>

          {/* Sample Rows Table */}
          <div>
            <h4 className="text-xs font-semibold text-slate-300 mb-2">Parsed Record Samples (First 10 Rows)</h4>
            <div className="overflow-x-auto rounded-lg border border-slate-800">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/90 text-slate-300 border-b border-slate-700">
                  <tr>
                    <th className="py-2 px-3">Date</th>
                    <th className="py-2 px-3">Order ID</th>
                    <th className="py-2 px-3">SKU</th>
                    <th className="py-2 px-3">Product Name</th>
                    <th className="py-2 px-3">Category</th>
                    <th className="py-2 px-3 text-right">Units</th>
                    <th className="py-2 px-3 text-right">Total ($)</th>
                    <th className="py-2 px-3 text-right">Profit ($)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {previewData.sample_rows?.map((row: any) => (
                    <tr key={row.id} className="hover:bg-slate-800/40">
                      <td className="py-2 px-3 font-mono text-slate-300">{row.date}</td>
                      <td className="py-2 px-3 font-mono text-primary">{row.order_id}</td>
                      <td className="py-2 px-3 font-mono text-slate-400">{row.sku}</td>
                      <td className="py-2 px-3 font-medium text-white truncate max-w-[200px]" title={row.product_name}>
                        {row.product_name}
                      </td>
                      <td className="py-2 px-3 text-slate-400">{row.category}</td>
                      <td className="py-2 px-3 text-right text-slate-200">{row.units_sold}</td>
                      <td className="py-2 px-3 text-right font-medium text-white">${row.total_sales.toFixed(2)}</td>
                      <td className="py-2 px-3 text-right">
                        {row.profit !== null && row.profit !== undefined ? (
                          <span className={row.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                            {row.profit < 0 ? '-' : ''}${Math.abs(row.profit).toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-slate-500">N/A</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
