'use client'

import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import api from '../../lib/api'
import {
  UploadCloud,
  FileText,
  Calendar,
  Table as TableIcon,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  X,
  ArrowRight,
  Database,
  Layers
} from 'lucide-react'

interface DataIngestionOverviewCardProps {
  onDataUploaded?: () => void
}

export default function DataIngestionOverviewCard({ onDataUploaded }: DataIngestionOverviewCardProps) {
  const queryClient = useQueryClient()

  const [previewData, setPreviewData] = useState<any>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [showTablePreview, setShowTablePreview] = useState(false)

  // Upload state
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [replaceExisting, setReplaceExisting] = useState(true)
  const [uploadMsg, setUploadMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [isDragging, setIsDragging] = useState(false)

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

  useEffect(() => {
    fetchPreview()
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) {
      if (!selected.name.endsWith('.csv')) {
        setUploadMsg({ type: 'error', text: 'Only .csv files are supported.' })
        return
      }
      setFile(selected)
      setUploadMsg(null)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const selected = e.dataTransfer.files?.[0]
    if (selected) {
      if (!selected.name.endsWith('.csv')) {
        setUploadMsg({ type: 'error', text: 'Only .csv files are supported.' })
        return
      }
      setFile(selected)
      setUploadMsg(null)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setUploadMsg({ type: 'error', text: 'Please select a CSV file first.' })
      return
    }

    setUploading(true)
    setUploadMsg(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await api.post(`/api/v1/data/upload?replace=${replaceExisting}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setUploadMsg({
        type: 'success',
        text: `Successfully processed ${res.data.records_processed?.toLocaleString()} sales records!`,
      })
      setFile(null)
      setShowUpload(false)
      fetchPreview()
      // Invalidate queries across overview dashboard
      queryClient.invalidateQueries()
      if (onDataUploaded) {
        onDataUploaded()
      }
    } catch (err: any) {
      setUploadMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to upload and ingest dataset.',
      })
    } finally {
      setUploading(false)
    }
  }

  const hasData = previewData?.has_data && (previewData?.row_count ?? 0) > 0

  return (
    <div className="bg-surface border border-slate-700/80 rounded-2xl p-5 shadow-lg space-y-4 transition-all">
      {/* Top Banner & Telemetry Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary flex-shrink-0">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-white">Data Ingestion & Dataset Preview</h3>
              {hasData ? (
                <span className="inline-flex items-center gap-1 text-[11px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full font-semibold">
                  <CheckCircle2 className="w-3 h-3" />
                  {previewData.row_count?.toLocaleString()} Records Loaded
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] bg-amber-500/15 text-amber-400 border border-amber-500/30 px-2.5 py-0.5 rounded-full font-semibold">
                  <AlertCircle className="w-3 h-3" />
                  No Dataset Ingested
                </span>
              )}
            </div>

            {hasData ? (
              <p className="text-xs text-slate-400 mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1">
                <span>File: <strong className="text-slate-200">{previewData.filename}</strong></span>
                <span>•</span>
                <span>Coverage: <strong className="text-slate-200">{previewData.date_coverage?.min_date}</strong> to <strong className="text-slate-200">{previewData.date_coverage?.max_date}</strong> ({previewData.date_coverage?.span_days} days)</span>
                <span>•</span>
                <span>Catalog: <strong className="text-slate-200">{previewData.product_count?.toLocaleString()} SKUs</strong> across <strong className="text-slate-200">{previewData.category_count} Categories</strong></span>
              </p>
            ) : (
              <p className="text-xs text-slate-400 mt-0.5">
                Upload your transaction CSV below to populate all 10 analytics modules with empirical store metrics.
              </p>
            )}
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap self-start sm:self-auto">
          <button
            type="button"
            onClick={() => {
              setShowUpload(!showUpload)
              if (!showUpload) setShowTablePreview(false)
            }}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
              showUpload
                ? 'bg-primary text-white border-primary shadow-sm'
                : 'bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            {showUpload ? 'Close Upload' : 'Quick Ingest CSV'}
          </button>

          {hasData && (
            <button
              type="button"
              onClick={() => {
                setShowTablePreview(!showTablePreview)
                if (!showTablePreview) setShowUpload(false)
              }}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                showTablePreview
                  ? 'bg-primary text-white border-primary shadow-sm'
                  : 'bg-slate-800 text-slate-200 border-slate-700 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              {showTablePreview ? 'Hide Preview' : 'Preview 10 Rows'}
            </button>
          )}

          <button
            type="button"
            onClick={fetchPreview}
            disabled={loadingPreview}
            title="Refresh dataset telemetry"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white bg-slate-800 border border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingPreview ? 'animate-spin text-primary' : ''}`} />
          </button>

          <Link
            href="/data"
            className="inline-flex items-center gap-1 text-xs text-primary font-semibold hover:underline px-2 py-1"
          >
            Data Center <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* Upload Feedback Alert */}
      {uploadMsg && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-center justify-between ${
            uploadMsg.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-danger/10 border-danger/40 text-danger'
          }`}
        >
          <div className="flex items-center gap-2">
            {uploadMsg.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-danger" />
            )}
            <span>{uploadMsg.text}</span>
          </div>
          <button
            type="button"
            onClick={() => setUploadMsg(null)}
            className="text-slate-400 hover:text-white text-xs"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* QUICK INGESTION ACCORDION PANEL */}
      {showUpload && (
        <div className="bg-background/80 border border-slate-700 rounded-xl p-5 space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-slate-700/60 pb-2">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
              <UploadCloud className="w-4 h-4 text-primary" />
              Upload & Replace Store Dataset
            </h4>
            <span className="text-[11px] text-slate-400">
              Supports Superstore, Kaggle, Shopify, and standard retail CSVs
            </span>
          </div>

          <form onSubmit={handleUpload} className="space-y-4">
            <div
              onDragOver={(e) => {
                e.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center space-y-2 ${
                isDragging
                  ? 'border-primary bg-primary/10'
                  : 'border-slate-700 hover:border-slate-500 bg-surface/50'
              }`}
              onClick={() => document.getElementById('overview-csv-input')?.click()}
            >
              <input
                id="overview-csv-input"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleFileChange}
              />
              <div className="w-12 h-12 rounded-xl bg-slate-800 text-primary flex items-center justify-center">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-200 font-medium">
                  {file ? (
                    <span className="text-emerald-400 font-bold">{file.name}</span>
                  ) : (
                    'Click to choose a CSV or drag and drop file here'
                  )}
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Canonical headers (date, sku/product, units_sold, sales, profit) auto-mapped'}
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-300">
                <input
                  type="checkbox"
                  checked={replaceExisting}
                  onChange={(e) => setReplaceExisting(e.target.checked)}
                  className="rounded border-slate-700 text-primary focus:ring-primary bg-slate-800"
                />
                <span>Wipe prior records to prevent appending duplicates (Recommended)</span>
              </label>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setFile(null)
                    setShowUpload(false)
                  }}
                  className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!file || uploading}
                  className="bg-primary hover:bg-blue-600 disabled:opacity-50 text-white font-semibold text-xs px-4 py-2 rounded-lg transition inline-flex items-center gap-2 shadow"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Parsing & Ingesting...
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-3.5 h-3.5" />
                      Ingest Dataset Now
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* DATASET 10-ROW TABLE PREVIEW PANEL */}
      {showTablePreview && previewData && (
        <div className="bg-background/90 border border-slate-700 rounded-xl p-5 space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between border-b border-slate-700/60 pb-3">
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <TableIcon className="w-4 h-4 text-primary" />
                Sample Parsed Transaction Ledger (10 Records)
              </h4>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Verified schema types with missing-value detection across {previewData.column_count} canonical database attributes.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowTablePreview(false)}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Schema Tags Bar */}
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            {previewData.columns?.map((col: any, idx: number) => (
              <span
                key={idx}
                className="bg-slate-800/80 border border-slate-700 text-slate-300 px-2 py-0.5 rounded font-mono"
              >
                {col.name} <span className="text-primary font-semibold">({col.type})</span>
              </span>
            ))}
          </div>

          {/* 10 Sample Rows Table */}
          {previewData.sample_rows && previewData.sample_rows.length > 0 ? (
            <div className="border border-slate-700/80 rounded-lg overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-800/80 text-slate-400 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-700">
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Order ID</th>
                    <th className="py-2.5 px-3">SKU</th>
                    <th className="py-2.5 px-3">Product Name</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Sub-Category</th>
                    <th className="py-2.5 px-3 text-right">Units</th>
                    <th className="py-2.5 px-3 text-right">Sales ($)</th>
                    <th className="py-2.5 px-3 text-right">Profit ($)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono text-[11px] bg-background/40">
                  {previewData.sample_rows.map((row: any, rIdx: number) => (
                    <tr key={rIdx} className="hover:bg-slate-800/40 transition">
                      <td className="py-2 px-3 text-slate-300 whitespace-nowrap">{row.date}</td>
                      <td className="py-2 px-3 text-primary truncate max-w-[120px]">{row.order_id || 'N/A'}</td>
                      <td className="py-2 px-3 text-slate-300 font-semibold">{row.sku}</td>
                      <td className="py-2 px-3 text-white truncate max-w-[180px] font-sans" title={row.product_name}>
                        {row.product_name || row.sku}
                      </td>
                      <td className="py-2 px-3 text-slate-400 font-sans">{row.category || 'General'}</td>
                      <td className="py-2 px-3 text-slate-400 font-sans">{row.sub_category || 'General'}</td>
                      <td className="py-2 px-3 text-right text-slate-200 font-bold">{row.units_sold}</td>
                      <td className="py-2 px-3 text-right text-emerald-400 font-bold">
                        ${row.total_sales != null ? Number(row.total_sales).toFixed(2) : '0.00'}
                      </td>
                      <td className={`py-2 px-3 text-right font-bold ${
                        row.profit == null
                          ? 'text-slate-500'
                          : Number(row.profit) >= 0
                          ? 'text-emerald-400'
                          : 'text-danger'
                      }`}>
                        {row.profit != null ? `$${Number(row.profit).toFixed(2)}` : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500 text-center py-4">
              No parsed sample rows found.
            </p>
          )}

          <div className="flex justify-between items-center text-[11px] text-slate-400 pt-1">
            <span>Showing first 10 parsed ledger rows</span>
            <Link
              href="/data"
              className="text-primary hover:underline font-semibold inline-flex items-center gap-1"
            >
              Open Full Data Ingestion & Audit Register &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

