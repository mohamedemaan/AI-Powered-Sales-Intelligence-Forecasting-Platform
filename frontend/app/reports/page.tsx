'use client'

import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'
import {
  FileText,
  Download,
  Printer,
  Calendar,
  CalendarDays,
  Package,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Search,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  BarChart3,
  ChevronDown,
  Clock,
  ArrowRight,
  ShieldCheck,
  Layers,
  Sparkles
} from 'lucide-react'
import Link from 'next/link'

interface ProductOption {
  sku: string
  product_name: string
  label: string
  count: number
  min_date?: string | null
  max_date?: string | null
}

interface CategoryBreakdownRow {
  category: string
  sub_category: string
  total_orders: number
  total_quantity_sold: number
  total_sales_usd: number
  total_profit_usd?: number | null
  profit_margin_pct?: number | null
}

interface ProfessionalReportResponse {
  report_metadata: {
    report_title: string
    generated_at: string
    filename: string
    summary_filename: string
    analysis_mode: string
    mode_type: string
    selected_date?: string | null
    start_date?: string | null
    end_date?: string | null
    target_product: string
    currency: string
    total_records_included: number
    has_data: boolean
    empty_reason?: string | null
    data_coverage_period: {
      min_date?: string | null
      max_date?: string | null
      total_store_records?: number
    }
    features_available: {
      has_category: boolean
      has_sub_category: boolean
      has_order_id: boolean
      has_profit: boolean
      has_sales: boolean
    }
    missing_data_notes: string[]
  }
  summary: {
    total_revenue: number
    total_distinct_orders: number
    total_quantity_sold: number
    total_profit?: number | null
    overall_profit_margin_pct?: number | null
    total_categories: number
    total_sub_categories: number
    total_skus_analyzed: number
    total_records_analyzed: number
  }
  category_breakdown: CategoryBreakdownRow[]
  detail_csv: string
  summary_csv: string
}

export default function ReportsPage() {
  // 1. Target Name & Scope Controls
  const [targetName, setTargetName] = useState('All Products (Global Aggregate)')
  const [selectedSku, setSelectedSku] = useState('ALL')
  const [productSearch, setProductSearch] = useState('')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [customInputMode, setCustomInputMode] = useState(false)

  // 2. Horizon Mode & Dates
  const [mode, setMode] = useState<'single' | 'range'>('range')
  const [selectedDate, setSelectedDate] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // 3. Execution & Reporting State
  const [isGenerating, setIsGenerating] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [reportData, setReportData] = useState<ProfessionalReportResponse | null>(null)

  // 4. Interactive Table Filtering & Sorting
  const [tableSearch, setTableSearch] = useState('')
  const [sortField, setSortField] = useState<keyof CategoryBreakdownRow>('total_sales_usd')
  const [sortAsc, setSortAsc] = useState(false)

  // Fetch available products & dataset metadata
  const { data: products, isLoading: loadingProducts } = useQuery<ProductOption[]>({
    queryKey: ['available-products'],
    queryFn: async () => {
      const res = await api.get('/api/v1/data/products')
      return res.data
    }
  })

  // Parse initial query params if deep-linked from Forecast Lab
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      const qMode = params.get('mode')
      const qSelected = params.get('selected_date') || params.get('date')
      const qStart = params.get('start_date') || params.get('start')
      const qEnd = params.get('end_date') || params.get('end')
      const qTarget = params.get('target_name') || params.get('target')

      if (qMode === 'single' || qMode === 'range') setMode(qMode)
      if (qSelected) setSelectedDate(qSelected)
      if (qStart) setStartDate(qStart)
      if (qEnd) setEndDate(qEnd)
      if (qTarget) {
        setTargetName(qTarget)
        setSelectedSku(qTarget)
      }
    }
  }, [])

  // Initialize dates when products metadata is loaded
  useEffect(() => {
    if (products && products.length > 0) {
      const globalMeta = products.find((p) => p.sku === 'ALL') || products[0]
      const maxD = globalMeta.max_date || new Date().toISOString().split('T')[0]
      const minD = globalMeta.min_date || '2014-01-01'

      if (!selectedDate) setSelectedDate(maxD)
      if (!endDate) setEndDate(maxD)
      if (!startDate) setStartDate(minD)
    }
  }, [products, selectedDate, startDate, endDate])

  // Filter products for dropdown
  const filteredProducts = useMemo(() => {
    if (!products) return []
    if (!productSearch.trim()) return products.slice(0, 50)
    const term = productSearch.toLowerCase()
    return products
      .filter(
        (p) =>
          p.product_name.toLowerCase().includes(term) ||
          p.sku.toLowerCase().includes(term) ||
          p.label.toLowerCase().includes(term)
      )
      .slice(0, 50)
  }, [products, productSearch])

  const handleSelectProduct = (p: ProductOption) => {
    setTargetName(p.product_name)
    setSelectedSku(p.sku)
    setIsDropdownOpen(false)
    setProductSearch('')
  }

  // Quick preset handlers
  const handlePresetSingle = (daysOffset: number) => {
    const globalMeta = products?.find((p) => p.sku === 'ALL')
    const maxD = globalMeta?.max_date || '2017-12-30'
    const d = new Date(maxD)
    d.setDate(d.getDate() + daysOffset)
    setSelectedDate(d.toISOString().split('T')[0])
  }

  const handlePresetRange = (daysBack: number) => {
    const globalMeta = products?.find((p) => p.sku === 'ALL')
    const maxD = globalMeta?.max_date || '2017-12-30'
    const minD = globalMeta?.min_date || '2014-01-01'

    if (daysBack === 0) {
      // Full dataset
      setStartDate(minD)
      setEndDate(maxD)
    } else {
      const endObj = new Date(maxD)
      const startObj = new Date(maxD)
      startObj.setDate(startObj.getDate() - daysBack)
      setStartDate(startObj.toISOString().split('T')[0])
      setEndDate(endObj.toISOString().split('T')[0])
    }
  }

  // Trigger report generation
  const handleGenerateReport = async () => {
    setErrorMsg(null)

    if (mode === 'range') {
      if (!startDate || !endDate) {
        setErrorMsg('Please specify both Start Date and End Date for Date Range report.')
        return
      }
      if (startDate > endDate) {
        setErrorMsg(`Start Date (${startDate}) cannot be after End Date (${endDate}).`)
        return
      }
    } else {
      if (!selectedDate) {
        setErrorMsg('Please select a Target Date for Selected Date report.')
        return
      }
    }

    setIsGenerating(true)

    try {
      const res = await api.post('/api/v1/analytics/report', {
        target_name: selectedSku === 'ALL' ? 'ALL' : (selectedSku || targetName),
        mode,
        selected_date: selectedDate,
        start_date: startDate,
        end_date: endDate
      })

      setReportData(res.data)
      if (!res.data.report_metadata.has_data) {
        setErrorMsg(res.data.report_metadata.empty_reason || 'No records matched your filter criteria.')
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to generate professional sales report.')
    } finally {
      setIsGenerating(false)
    }
  }

  // Download Detail CSV
  const handleDownloadDetailCSV = () => {
    if (!reportData?.detail_csv) return
    const filename = reportData.report_metadata.filename || `professional_sales_summary_${new Date().toISOString().slice(0, 10)}.csv`
    const blob = new Blob([reportData.detail_csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Download Summary CSV
  const handleDownloadSummaryCSV = () => {
    if (!reportData?.summary_csv) return
    const filename = reportData.report_metadata.summary_filename || `professional_sales_summary_summary_${new Date().toISOString().slice(0, 10)}.csv`
    const blob = new Blob([reportData.summary_csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Download Full JSON
  const handleDownloadJSON = () => {
    if (!reportData) return
    const dateStr = new Date().toISOString().slice(0, 10)
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `professional_sales_report_${dateStr}.json`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Print / Save to PDF
  const handlePrintPDF = () => {
    window.print()
  }

  // Filtered & sorted table data
  const processedRows = useMemo(() => {
    if (!reportData?.category_breakdown) return []
    let rows = [...reportData.category_breakdown]

    if (tableSearch.trim()) {
      const term = tableSearch.toLowerCase()
      rows = rows.filter(
        (r) =>
          r.category.toLowerCase().includes(term) ||
          r.sub_category.toLowerCase().includes(term)
      )
    }

    rows.sort((a: any, b: any) => {
      let va = a[sortField]
      let vb = b[sortField]

      if (va == null) return 1
      if (vb == null) return -1

      if (typeof va === 'string') {
        return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va)
      }
      return sortAsc ? va - vb : vb - va
    })

    return rows
  }, [reportData, tableSearch, sortField, sortAsc])

  const datasetInfo = products?.find((p) => p.sku === 'ALL')

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {/* Page Header */}
      <header className="border-b border-slate-800 pb-6 print:border-none">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-3xl font-extrabold text-white tracking-tight">
                Reports &amp; Export Center
              </h2>
              <span className="text-xs bg-gradient-to-r from-blue-500/20 to-indigo-500/20 text-blue-300 border border-blue-500/40 font-semibold px-2.5 py-0.5 rounded-full">
                Professional BI Suite
              </span>
            </div>
            <p className="text-slate-400 text-sm">
              Generate audited category and sub-category performance summaries, order volume metrics, revenue telemetry, and profit margins.
            </p>
          </div>

          {datasetInfo && datasetInfo.min_date && datasetInfo.max_date && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-xs flex items-center gap-2 text-slate-300 print:hidden">
              <Clock className="h-4 w-4 text-primary" />
              <span>
                Dataset Coverage:{' '}
                <strong className="text-white font-mono">{datasetInfo.min_date}</strong> to{' '}
                <strong className="text-white font-mono">{datasetInfo.max_date}</strong> ({datasetInfo.count.toLocaleString()} records)
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Control Panel: Product & Horizon Controls (Reusing Forecast Lab patterns) */}
      <section className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-6 print:hidden">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-primary" />
            <h3 className="text-base font-bold text-white">Report Configuration &amp; Scope</h3>
          </div>
          <span className="text-xs text-slate-400">
            Export pattern: <code className="text-primary font-mono font-semibold">professional_sales_summary_YYYY-MM-DD.csv</code>
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Target Product Selector */}
          <div className="lg:col-span-5 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-white flex items-center gap-2">
                <Package className="h-4 w-4 text-primary" />
                Target Product Scope
              </label>
              <button
                type="button"
                onClick={() => {
                  setCustomInputMode(!customInputMode)
                  setIsDropdownOpen(false)
                }}
                className="text-xs text-primary hover:text-blue-400 transition underline underline-offset-2"
              >
                {customInputMode ? 'Choose from product list' : 'Type custom name / SKU'}
              </button>
            </div>

            {customInputMode ? (
              <div>
                <input
                  type="text"
                  value={targetName}
                  onChange={(e) => {
                    setTargetName(e.target.value)
                    setSelectedSku(e.target.value)
                  }}
                  placeholder="Enter Product Name or SKU (e.g. 'Staples' or 'ALL')..."
                  className="w-full bg-background text-white px-4 py-2.5 rounded-xl border border-slate-600 focus:outline-none focus:border-primary text-sm shadow-inner"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Type a product name or SKU. Use <code className="text-primary font-mono">ALL</code> to aggregate entire store revenue.
                </p>
              </div>
            ) : (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  disabled={loadingProducts}
                  className="w-full bg-background text-white px-4 py-2.5 rounded-xl border border-slate-600 hover:border-slate-500 focus:outline-none focus:border-primary text-sm flex items-center justify-between text-left shadow-inner transition"
                >
                  <span className="truncate pr-2 font-medium">
                    {targetName || 'Select a product...'}
                  </span>
                  <div className="flex items-center gap-2 shrink-0">
                    {selectedSku !== 'ALL' && (
                      <span className="text-[10px] bg-slate-800 text-slate-300 font-mono px-2 py-0.5 rounded border border-slate-700">
                        {selectedSku}
                      </span>
                    )}
                    <ChevronDown className="h-4 w-4 text-slate-400" />
                  </div>
                </button>

                {isDropdownOpen && (
                  <div className="absolute z-50 left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden max-h-80 flex flex-col">
                    <div className="p-2 border-b border-slate-800 bg-slate-950/70">
                      <div className="relative">
                        <Search className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-3" />
                        <input
                          type="text"
                          value={productSearch}
                          onChange={(e) => setProductSearch(e.target.value)}
                          placeholder="Search products by name or SKU..."
                          className="w-full bg-slate-900 text-white pl-9 pr-3 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-primary text-xs"
                          autoFocus
                        />
                      </div>
                    </div>
                    <div className="overflow-y-auto divide-y divide-slate-800/60 max-h-60 text-xs">
                      {filteredProducts.map((p) => (
                        <button
                          key={p.sku}
                          type="button"
                          onClick={() => handleSelectProduct(p)}
                          className={`w-full text-left px-3.5 py-2.5 hover:bg-slate-800 transition flex items-center justify-between ${
                            selectedSku === p.sku ? 'bg-primary/20 text-white font-semibold' : 'text-slate-300'
                          }`}
                        >
                          <span className="truncate pr-2">{p.label}</span>
                          <span className="text-[10px] bg-slate-800 text-slate-400 font-mono px-1.5 py-0.5 rounded shrink-0 border border-slate-700">
                            {p.count} recs
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Analysis Horizon Mode */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-white flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                Analysis Horizon Mode
              </label>

              {/* Mode Toggle */}
              <div className="inline-flex bg-background p-1 rounded-xl border border-slate-700 text-xs">
                <button
                  type="button"
                  onClick={() => setMode('single')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition font-medium ${
                    mode === 'single' ? 'bg-primary text-white shadow' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Calendar className="h-3.5 w-3.5" />
                  Option A: Selected Date
                </button>
                <button
                  type="button"
                  onClick={() => setMode('range')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition font-medium ${
                    mode === 'range' ? 'bg-primary text-white shadow' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <CalendarDays className="h-3.5 w-3.5" />
                  Option B: Date Range
                </button>
              </div>
            </div>

            {/* Date Inputs based on Mode */}
            {mode === 'single' ? (
              <div className="bg-background/60 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Target Analysis Date</label>
                    <input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono shadow-inner"
                    />
                  </div>
                  <div className="flex items-center gap-2 self-end">
                    <span className="text-[11px] text-slate-500">Quick Presets:</span>
                    <button
                      type="button"
                      onClick={() => handlePresetSingle(0)}
                      className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition"
                    >
                      Latest Recorded
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-background/60 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Start Date (Inclusive)</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono shadow-inner"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">End Date (Inclusive)</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono shadow-inner"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/80">
                  <span className="text-[11px] text-slate-500">Quick Presets:</span>
                  <button
                    type="button"
                    onClick={() => handlePresetRange(0)}
                    className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition"
                  >
                    Full Dataset Coverage
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePresetRange(30)}
                    className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition"
                  >
                    Last 30 Days
                  </button>
                  <button
                    type="button"
                    onClick={() => handlePresetRange(90)}
                    className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition"
                  >
                    Last 90 Days
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            onClick={handleGenerateReport}
            disabled={isGenerating || (mode === 'range' && !!startDate && !!endDate && startDate > endDate)}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3 px-8 rounded-xl shadow-lg transition-all flex items-center gap-2.5 disabled:opacity-50 text-sm"
          >
            {isGenerating ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Compiling Professional Report...</span>
              </>
            ) : (
              <>
                <FileText className="h-4 w-4" />
                <span>Generate Professional Sales Report</span>
              </>
            )}
          </button>
        </div>
      </section>

      {/* Error or Empty Alert */}
      {errorMsg && (
        <div className="p-4 bg-danger/10 border border-danger/40 text-danger rounded-xl text-sm flex items-start gap-3 shadow-md print:hidden">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-danger mb-0.5">Report Notice</h4>
            <p>{errorMsg}</p>
          </div>
        </div>
      )}

      {/* REPORT PRESENTATION SECTION */}
      {reportData && reportData.report_metadata.has_data && (
        <div className="space-y-8 animate-fadeIn">
          {/* Executive Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-surface p-5 rounded-2xl border border-slate-700 shadow-md">
              <span className="text-xs text-slate-400 block mb-1">Total Tracked Revenue</span>
              <div className="text-2xl font-black text-white">
                ${reportData.summary.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Filtered commercial sales
              </span>
            </div>

            <div className="bg-surface p-5 rounded-2xl border border-slate-700 shadow-md">
              <span className="text-xs text-slate-400 block mb-1">Total Distinct Orders</span>
              <div className="text-2xl font-black text-white">
                {reportData.summary.total_distinct_orders.toLocaleString()}
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                {reportData.report_metadata.features_available.has_order_id ? 'Unique Order IDs' : 'Transaction lines (Proxy)'}
              </span>
            </div>

            <div className="bg-surface p-5 rounded-2xl border border-slate-700 shadow-md">
              <span className="text-xs text-slate-400 block mb-1">Total Quantity Sold</span>
              <div className="text-2xl font-black text-white">
                {reportData.summary.total_quantity_sold.toLocaleString()} units
              </div>
              <span className="text-[11px] text-slate-500 mt-1 block">
                Across {reportData.summary.total_skus_analyzed.toLocaleString()} unique SKUs
              </span>
            </div>

            <div className="bg-surface p-5 rounded-2xl border border-slate-700 shadow-md">
              <span className="text-xs text-slate-400 block mb-1">Total Profit &amp; Margin</span>
              <div className="text-2xl font-black text-white">
                {reportData.summary.total_profit != null
                  ? `$${reportData.summary.total_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                  : 'N/A'}
              </div>
              <div className="mt-1 flex items-center gap-1.5">
                {reportData.summary.overall_profit_margin_pct != null ? (
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      reportData.summary.overall_profit_margin_pct >= 0
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'bg-danger/20 text-danger border border-danger/40'
                    }`}
                  >
                    {reportData.summary.overall_profit_margin_pct >= 0 ? '+' : ''}
                    {reportData.summary.overall_profit_margin_pct}% Margin
                  </span>
                ) : (
                  <span className="text-xs text-slate-500">Margin N/A (Missing Profit Data)</span>
                )}
              </div>
            </div>
          </div>

          {/* Action Center: Export Formats & Delivery */}
          <div className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-4 print:hidden">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <h4 className="text-lg font-bold text-white flex items-center gap-2">
                  <Download className="h-5 w-5 text-emerald-400" />
                  Export Delivery Center
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Download audited CSV reports or print professional PDF documentation for business reviews.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={handleDownloadDetailCSV}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition shadow flex items-center gap-2"
                  title="Download clean Category & Sub-Category table as CSV"
                >
                  <Download className="h-4 w-4" />
                  Download Detail CSV ({reportData.report_metadata.filename})
                </button>

                <button
                  onClick={handleDownloadSummaryCSV}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3.5 py-2.5 rounded-xl transition flex items-center gap-2"
                  title="Download high-level summary KPIs and metadata"
                >
                  <FileText className="h-4 w-4" />
                  Download Summary CSV
                </button>

                <button
                  onClick={handleDownloadJSON}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3 py-2.5 rounded-xl transition flex items-center gap-1.5"
                >
                  JSON
                </button>

                <button
                  onClick={handlePrintPDF}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-3.5 py-2.5 rounded-xl transition flex items-center gap-2"
                >
                  <Printer className="h-4 w-4 text-slate-400" />
                  Print / Save as PDF
                </button>
              </div>
            </div>

            {/* Manifest Bar */}
            <div className="flex flex-wrap items-center gap-y-2 gap-x-6 text-xs text-slate-400 pt-1">
              <span>
                Generated: <strong className="text-slate-200 font-mono">{reportData.report_metadata.generated_at}</strong>
              </span>
              <span>•</span>
              <span>
                Analysis Horizon: <strong className="text-slate-200">{reportData.report_metadata.analysis_mode}</strong>
              </span>
              <span>•</span>
              <span>
                Transactions Analysed:{' '}
                <strong className="text-white font-mono">{reportData.summary.total_records_analyzed.toLocaleString()}</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 text-emerald-400 font-medium">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Data Verified
              </span>
            </div>

            {reportData.report_metadata.missing_data_notes.length > 0 && (
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <span className="font-semibold text-slate-300 block">Dataset Schema Notes:</span>
                {reportData.report_metadata.missing_data_notes.map((note, idx) => (
                  <p key={idx}>• {note}</p>
                ))}
              </div>
            )}
          </div>

          {/* Category & Sub-Category Performance Table */}
          <div className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
              <div>
                <h4 className="text-lg font-bold text-white flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Category &amp; Sub-Category Commercial Performance
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Sorted by sales volume. Click headers to adjust column sorting.
                </p>
              </div>

              <div className="relative print:hidden">
                <Search className="h-4 w-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={tableSearch}
                  onChange={(e) => setTableSearch(e.target.value)}
                  placeholder="Filter category or sub-category..."
                  className="bg-slate-900 text-white pl-9 pr-3 py-2 rounded-xl border border-slate-700 focus:outline-none focus:border-primary text-xs w-64 shadow-inner"
                />
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400 uppercase tracking-wider font-semibold bg-slate-900/50">
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-white"
                      onClick={() => {
                        setSortField('category')
                        setSortAsc(!sortAsc)
                      }}
                    >
                      Category {sortField === 'category' ? (sortAsc ? '▲' : '▼') : ''}
                    </th>
                    <th
                      className="py-3 px-4 cursor-pointer hover:text-white"
                      onClick={() => {
                        setSortField('sub_category')
                        setSortAsc(!sortAsc)
                      }}
                    >
                      Sub-Category {sortField === 'sub_category' ? (sortAsc ? '▲' : '▼') : ''}
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-white"
                      onClick={() => {
                        setSortField('total_orders')
                        setSortAsc(!sortAsc)
                      }}
                    >
                      Total Orders {sortField === 'total_orders' ? (sortAsc ? '▲' : '▼') : ''}
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-white"
                      onClick={() => {
                        setSortField('total_quantity_sold')
                        setSortAsc(!sortAsc)
                      }}
                    >
                      Total Quantity Sold {sortField === 'total_quantity_sold' ? (sortAsc ? '▲' : '▼') : ''}
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-white"
                      onClick={() => {
                        setSortField('total_sales_usd')
                        setSortAsc(!sortAsc)
                      }}
                    >
                      Total Sales (USD) {sortField === 'total_sales_usd' ? (sortAsc ? '▲' : '▼') : ''}
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-white"
                      onClick={() => {
                        setSortField('total_profit_usd')
                        setSortAsc(!sortAsc)
                      }}
                    >
                      Total Profit (USD) {sortField === 'total_profit_usd' ? (sortAsc ? '▲' : '▼') : ''}
                    </th>
                    <th
                      className="py-3 px-4 text-right cursor-pointer hover:text-white"
                      onClick={() => {
                        setSortField('profit_margin_pct')
                        setSortAsc(!sortAsc)
                      }}
                    >
                      Profit Margin (%) {sortField === 'profit_margin_pct' ? (sortAsc ? '▲' : '▼') : ''}
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800 font-mono">
                  {processedRows.map((row, idx) => {
                    const isProfitLoss = row.total_profit_usd != null && row.total_profit_usd < 0
                    const isHighMargin = row.profit_margin_pct != null && row.profit_margin_pct >= 20.0

                    return (
                      <tr key={idx} className="hover:bg-slate-800/40 transition font-sans">
                        <td className="py-3 px-4 font-semibold text-white">{row.category}</td>
                        <td className="py-3 px-4 text-slate-300 font-medium">{row.sub_category}</td>
                        <td className="py-3 px-4 text-right font-mono text-slate-200">
                          {row.total_orders.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-slate-200">
                          {row.total_quantity_sold.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-white">
                          ${row.total_sales_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-right font-mono font-medium">
                          {row.total_profit_usd != null ? (
                            <span className={isProfitLoss ? 'text-danger font-bold' : 'text-slate-200'}>
                              ${row.total_profit_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {row.profit_margin_pct != null ? (
                            <span
                              className={`text-[11px] font-bold px-2 py-0.5 rounded-full inline-block ${
                                isProfitLoss
                                  ? 'bg-danger/20 text-danger border border-danger/40'
                                  : isHighMargin
                                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                              }`}
                            >
                              {row.profit_margin_pct >= 0 ? '+' : ''}
                              {row.profit_margin_pct.toFixed(2)}%
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[11px]">N/A</span>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>

                {/* Footer Totals */}
                <tfoot>
                  <tr className="border-t-2 border-slate-700 bg-slate-900/80 font-bold text-white">
                    <td className="py-3 px-4 uppercase tracking-wider text-xs">Total / Aggregate</td>
                    <td className="py-3 px-4 text-slate-400 text-xs font-normal">
                      {reportData.summary.total_sub_categories} Sub-Categories
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {reportData.summary.total_distinct_orders.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {reportData.summary.total_quantity_sold.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-emerald-400 text-sm">
                      ${reportData.summary.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {reportData.summary.total_profit != null
                        ? `$${reportData.summary.total_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                        : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right font-mono">
                      {reportData.summary.overall_profit_margin_pct != null ? (
                        <span className="text-emerald-400">
                          {reportData.summary.overall_profit_margin_pct.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-slate-500">N/A</span>
                      )}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Initial Empty State before generation */}
      {!reportData && !isGenerating && (
        <div className="bg-surface/50 border border-dashed border-slate-700 rounded-2xl p-12 text-center space-y-4 print:hidden">
          <div className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mx-auto shadow-inner">
            <FileText className="h-8 w-8" />
          </div>
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-semibold text-white">Ready to Compile Professional Sales Report</h3>
            <p className="text-xs text-slate-400 mt-1">
              Select your Target Product Scope, choose between <strong>Option A (Selected Date)</strong> or <strong>Option B (Date Range)</strong>, and click <em>Generate Professional Sales Report</em> to build RFC-compliant CSVs and executive telemetry.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
