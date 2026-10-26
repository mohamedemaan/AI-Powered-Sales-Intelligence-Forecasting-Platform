'use client'

import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'
import dynamic from 'next/dynamic'
import {
  Calendar,
  CalendarDays,
  Cpu,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Package,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Search,
  ChevronDown,
  Clock,
  ArrowRight,
  ShieldCheck,
  BarChart3,
  RefreshCw,
  Info,
  Download
} from 'lucide-react'
import Link from 'next/link'

const ForecastChart = dynamic(() => import('../../components/charts/ForecastChart'), {
  ssr: false,
  loading: () => (
    <div className="h-80 w-full flex items-center justify-center text-slate-500">
      <p className="animate-pulse">Loading visualization engine...</p>
    </div>
  ),
})

interface ProductOption {
  sku: string
  product_name: string
  label: string
  count: number
  min_date?: string | null
  max_date?: string | null
}

interface AnalysisReport {
  summary: {
    target_name: string
    sku: string
    mode: string
    selected_date?: string | null
    start_date?: string | null
    end_date?: string | null
    data_points_analyzed: number
    status: string
    is_forecast: boolean
    model_used: string
    generated_at: string
    dataset_coverage: {
      min_date: string
      max_date: string
    }
  }
  sales_performance: {
    total_revenue: number
    total_units: number
    avg_daily_sales: number
    avg_unit_price: number
    highest_sales_date?: { date: string; units: number; revenue: number } | null
    lowest_sales_date?: { date: string; units: number; revenue: number } | null
    growth_vs_prior_period_pct?: number | null
    prior_period_revenue?: number | null
    historical_comparisons?: {
      previous_day_pct?: number | null
      previous_week_pct?: number | null
      trailing_30d_avg_units?: number | null
    } | null
  }
  forecast_results: {
    is_applicable: boolean
    model_name: string
    predicted_units?: number | null
    predicted_revenue?: number | null
    lower_bound?: number | null
    upper_bound?: number | null
    evaluation_metrics: {
      mae?: number | null
      rmse?: number | null
      wape?: number | null
    }
    explanation: string
    limitations: string
  }
  chart_data: Array<{
    date: string
    full_date: string
    actual?: number | null
    forecast?: number | null
    lower?: number | null
    upper?: number | null
  }>
  insights: Array<{
    type: string
    title: string
    description: string
  }>
}

export default function ForecastLabPage() {
  // 1. Target Name & Product Selection
  const [targetName, setTargetName] = useState('All Products (Global Aggregate)')
  const [selectedSku, setSelectedSku] = useState('ALL')
  const [productSearch, setProductSearch] = useState('')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [customInputMode, setCustomInputMode] = useState(false)

  // 2. Date Selection Mode ('single' or 'range')
  const [mode, setMode] = useState<'single' | 'range'>('range')
  const [selectedDate, setSelectedDate] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  // 3. Model Preference
  const [modelPreference, setModelPreference] = useState<'auto' | 'baseline' | 'arima'>('auto')

  // 4. Execution State & Report Results
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExportingReport, setIsExportingReport] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [report, setReport] = useState<AnalysisReport | null>(null)

  // Fetch available products and dataset metadata
  const { data: products, isLoading: loadingProducts } = useQuery<ProductOption[]>({
    queryKey: ['available-products'],
    queryFn: async () => {
      const res = await api.get('/api/v1/data/products')
      return res.data
    }
  })

  // Initialize dates based on dataset metadata when products load
  useEffect(() => {
    if (products && products.length > 0) {
      const globalMeta = products.find((p) => p.sku === 'ALL') || products[0]
      const maxD = globalMeta.max_date || new Date().toISOString().split('T')[0]
      const minD = globalMeta.min_date || '2014-01-01'

      // Default single date to latest recorded date
      if (!selectedDate) {
        setSelectedDate(maxD)
      }

      // Default date range to last 30 days of the dataset
      if (!endDate) {
        setEndDate(maxD)
      }
      if (!startDate) {
        try {
          const endObj = new Date(maxD)
          endObj.setDate(endObj.getDate() - 30)
          const derivedStart = endObj.toISOString().split('T')[0]
          setStartDate(derivedStart < minD ? minD : derivedStart)
        } catch {
          setStartDate(minD)
        }
      }
    }
  }, [products, selectedDate, startDate, endDate])

  // Filter products for searchable dropdown
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
    // Update dates bounds if specific product has dates
    if (p.max_date && mode === 'single' && !selectedDate) {
      setSelectedDate(p.max_date)
    }
  }

  // Quick Preset Handlers
  const handlePresetSingle = (daysOffset: number) => {
    const globalMeta = products?.find((p) => p.sku === 'ALL')
    const maxD = globalMeta?.max_date || '2017-12-30'
    const d = new Date(maxD)
    d.setDate(d.getDate() + daysOffset)
    setSelectedDate(d.toISOString().split('T')[0])
  }

  const handlePresetRange = (daysBack: number, futureDays: number = 0) => {
    const globalMeta = products?.find((p) => p.sku === 'ALL')
    const maxD = globalMeta?.max_date || '2017-12-30'
    const endObj = new Date(maxD)
    endObj.setDate(endObj.getDate() + futureDays)
    const startObj = new Date(maxD)
    startObj.setDate(startObj.getDate() - daysBack)

    setStartDate(startObj.toISOString().split('T')[0])
    setEndDate(endObj.toISOString().split('T')[0])
  }

  // Submit Analysis Request
  const handleAnalyze = async () => {
    // 1. Validation
    setAnalysisError(null)

    if (mode === 'range') {
      if (!startDate || !endDate) {
        setAnalysisError('Please choose both a Start Date and an End Date for Date Range analysis.')
        return
      }
      if (startDate > endDate) {
        setAnalysisError(`Validation failed: Start Date (${startDate}) cannot be after End Date (${endDate}).`)
        return
      }
    } else {
      if (!selectedDate) {
        setAnalysisError('Please choose a valid Selected Date.')
        return
      }
    }

    setIsAnalyzing(true)

    try {
      const res = await api.post('/api/v1/ml/analyze', {
        target_name: selectedSku === 'ALL' ? 'ALL' : (selectedSku || targetName),
        mode,
        selected_date: selectedDate,
        start_date: startDate,
        end_date: endDate,
        model_preference: modelPreference,
      })

      setReport(res.data)
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setAnalysisError(
        typeof detail === 'string'
          ? detail
          : 'Failed to analyze sales data. Please check product selection or date inputs.'
      )
    } finally {
      setIsAnalyzing(false)
    }
  }

  // Quick Professional Sales Summary Report Export from Forecast Lab
  const handleExportProfessionalReport = async () => {
    setAnalysisError(null)
    if (mode === 'range') {
      if (!startDate || !endDate) {
        setAnalysisError('Please choose both a Start Date and an End Date to export the report.')
        return
      }
      if (startDate > endDate) {
        setAnalysisError(`Validation failed: Start Date (${startDate}) cannot be after End Date (${endDate}).`)
        return
      }
    } else {
      if (!selectedDate) {
        setAnalysisError('Please choose a valid Selected Date to export the report.')
        return
      }
    }

    setIsExportingReport(true)
    try {
      const res = await api.post('/api/v1/analytics/report', {
        target_name: selectedSku === 'ALL' ? 'ALL' : (selectedSku || targetName),
        mode,
        selected_date: selectedDate,
        start_date: startDate,
        end_date: endDate,
      })

      const detailCsv = res.data?.detail_csv
      const filename = res.data?.report_metadata?.filename || `professional_sales_summary_${new Date().toISOString().slice(0, 10)}.csv`

      if (detailCsv) {
        const blob = new Blob([detailCsv], { type: 'text/csv;charset=utf-8;' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      } else {
        setAnalysisError('No CSV content returned from reporting engine.')
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setAnalysisError(
        typeof detail === 'string'
          ? detail
          : 'Failed to generate professional sales report. Please check date inputs.'
      )
    } finally {
      setIsExportingReport(false)
    }
  }

  const datasetInfo = products?.find((p) => p.sku === 'ALL')

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <header className="border-b border-slate-800 pb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-3xl font-extrabold text-white tracking-tight">
                Forecast Lab & Model Selection
              </h2>
              <span className="text-xs bg-primary/20 text-primary border border-primary/40 font-semibold px-2.5 py-0.5 rounded-full">
                Production Engine
              </span>
            </div>
            <p className="text-slate-400 text-sm">
              Empirical historical ledger analysis, date-specific cross-validation, and forward trajectory forecasting.
            </p>
          </div>

          {datasetInfo && datasetInfo.min_date && datasetInfo.max_date && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-xs flex items-center gap-2 text-slate-300">
              <Clock className="h-4 w-4 text-primary" />
              <span>
                Dataset Ledger Coverage:{' '}
                <strong className="text-white font-mono">{datasetInfo.min_date}</strong> to{' '}
                <strong className="text-white font-mono">{datasetInfo.max_date}</strong> ({datasetInfo.count.toLocaleString()} records)
              </span>
            </div>
          )}
        </div>
      </header>

      {!loadingProducts && (!products || products.length === 0) && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-6 h-6 text-amber-400 shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-white">No sales dataset available</h4>
              <p className="text-xs text-slate-400 mt-0.5">Please import your transaction history in Data Ingestion before running forecasts and cross-validation.</p>
            </div>
          </div>
          <Link
            href="/data"
            className="text-xs bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/40 px-3.5 py-2 rounded-lg font-medium transition shrink-0"
          >
            Import Dataset &rarr;
          </Link>
        </div>
      )}

      {/* Control Panel: Target Name & Date Selection */}
      <section className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Target Name Product Selector */}
          <div className="lg:col-span-5 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-semibold text-white flex items-center gap-2">
                <Package className="h-4 w-4 text-primary" />
                Target Name
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

                    <div className="overflow-y-auto divide-y divide-slate-800/60 p-1">
                      {filteredProducts.length === 0 ? (
                        <div className="p-4 text-center text-xs text-slate-500">
                          No matching products found in dataset.
                        </div>
                      ) : (
                        filteredProducts.map((p) => {
                          const isSelected = p.sku === selectedSku
                          return (
                            <button
                              key={`${p.sku}-${p.product_name}`}
                              type="button"
                              onClick={() => handleSelectProduct(p)}
                              className={`w-full text-left p-2.5 rounded-lg text-xs flex items-center justify-between transition ${
                                isSelected
                                  ? 'bg-primary/20 text-white font-semibold'
                                  : 'text-slate-300 hover:bg-slate-800/70 hover:text-white'
                              }`}
                            >
                              <div className="truncate pr-3">
                                <div className="truncate text-slate-200">{p.product_name}</div>
                                {p.sku !== 'ALL' && (
                                  <div className="text-[10px] text-slate-500 font-mono">
                                    SKU: {p.sku}
                                  </div>
                                )}
                              </div>
                              <span className="shrink-0 text-[10px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700">
                                {p.count} records
                              </span>
                            </button>
                          )
                        })
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Date Selection Modes: Option A & Option B */}
          <div className="lg:col-span-7 space-y-4">
            <div>
              <span className="text-sm font-semibold text-white block mb-2">
                Analysis Date Horizon Mode
              </span>

              {/* Segmented Control */}
              <div className="grid grid-cols-2 gap-3 bg-background p-1.5 rounded-xl border border-slate-700/80">
                <button
                  type="button"
                  onClick={() => setMode('single')}
                  className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold transition ${
                    mode === 'single'
                      ? 'bg-primary text-white shadow-md'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  <Calendar className="h-4 w-4" />
                  <span>Option A: Selected Date</span>
                </button>

                <button
                  type="button"
                  onClick={() => setMode('range')}
                  className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold transition ${
                    mode === 'range'
                      ? 'bg-primary text-white shadow-md'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  <CalendarDays className="h-4 w-4" />
                  <span>Option B: Date Range</span>
                </button>
              </div>
            </div>

            {/* Conditional Date Inputs based on Mode */}
            {mode === 'single' ? (
              <div className="bg-background/60 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">
                      Choose Analysis Target Date
                    </label>
                    <input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono shadow-inner"
                    />
                  </div>

                  <div className="flex flex-wrap items-center gap-2 self-end">
                    <span className="text-[11px] text-slate-500">Quick Presets:</span>
                    <button
                      type="button"
                      onClick={() => handlePresetSingle(0)}
                      className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition"
                    >
                      Latest Recorded
                    </button>
                    <button
                      type="button"
                      onClick={() => handlePresetSingle(1)}
                      className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition"
                    >
                      Next Day (+1d)
                    </button>
                    <button
                      type="button"
                      onClick={() => handlePresetSingle(7)}
                      className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition"
                    >
                      Future (+7d)
                    </button>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                  <Info className="h-3.5 w-3.5 text-primary shrink-0" />
                  <span>
                    If date is in the historical ledger, actual transactions &amp; week-over-week deltas are displayed. If date is in the future, forward walk-forward ML models project demand.
                  </span>
                </div>
              </div>
            ) : (
              <div className="bg-background/60 p-4 rounded-xl border border-slate-800 space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Start Date</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono shadow-inner"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">End Date</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full bg-slate-900 text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono shadow-inner"
                    />
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="text-[11px] text-slate-500">Range Presets:</span>
                    <button
                      type="button"
                      onClick={() => handlePresetRange(30, 0)}
                      className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700 transition"
                    >
                      Last 30 Days
                    </button>
                    <button
                      type="button"
                      onClick={() => handlePresetRange(90, 0)}
                      className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700 transition"
                    >
                      Last 90 Days
                    </button>
                    <button
                      type="button"
                      onClick={() => handlePresetRange(14, 14)}
                      className="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-700 transition"
                    >
                      Actuals + Next 14d Forecast
                    </button>
                  </div>

                  {startDate && endDate && startDate > endDate && (
                    <span className="text-xs text-danger font-semibold">
                      ⚠ Start Date cannot be later than End Date
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Model Selection & Action Trigger */}
        <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400 font-medium">Model Engine:</label>
            <select
              value={modelPreference}
              onChange={(e) => setModelPreference(e.target.value as any)}
              className="bg-background text-white px-3 py-1.5 rounded-lg border border-slate-600 text-xs focus:outline-none focus:border-primary font-medium"
            >
              <option value="auto">Auto-Select (Walk-Forward Best Model)</option>
              <option value="arima">ARIMA (Auto-Regressive Integrated MA)</option>
              <option value="baseline">Seasonal Naive (snaive Baseline)</option>
            </select>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <button
              onClick={handleExportProfessionalReport}
              disabled={isExportingReport || (mode === 'range' && !!startDate && !!endDate && startDate > endDate)}
              type="button"
              className="w-full sm:w-auto bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 font-semibold py-3 px-5 rounded-xl transition text-xs flex items-center justify-center gap-2 disabled:opacity-50"
              title="Generate and download the Professional Sales Summary CSV for the selected date horizon"
            >
              {isExportingReport ? (
                <RefreshCw className="h-4 w-4 animate-spin text-primary" />
              ) : (
                <Download className="h-4 w-4 text-primary" />
              )}
              <span>Generate Professional Sales Report</span>
            </button>

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || (mode === 'range' && !!startDate && !!endDate && startDate > endDate)}
              className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold py-3 px-8 rounded-xl shadow-lg transition-all duration-200 flex items-center justify-center gap-2.5 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Running Empirical Analysis &amp; Forecast...</span>
                </>
              ) : (
                <>
                  <BarChart3 className="h-4 w-4" />
                  <span>Analyse &amp; Generate Report</span>
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      {/* Validation or Backend Error Alert */}
      {analysisError && (
        <div className="p-4 bg-danger/10 border border-danger/40 text-danger rounded-xl text-sm flex items-start gap-3 shadow-md">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-danger mb-0.5">Analysis Request Blocked</h4>
            <p>{analysisError}</p>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isAnalyzing && (
        <div className="bg-surface p-10 rounded-2xl border border-slate-800 text-center space-y-4">
          <RefreshCw className="h-10 w-10 text-primary animate-spin mx-auto" />
          <h3 className="text-lg font-semibold text-white">Synthesizing Sales Ledger</h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            Extracting historical transactions, executing walk-forward time-series validation, and generating grounded business metrics...
          </p>
        </div>
      )}

      {/* DETAILED ANALYSIS REPORT SECTION */}
      {report && !isAnalyzing && (
        <div className="space-y-8 animate-fadeIn">
          {/* Section A: Report Summary */}
          <div className="bg-surface p-6 rounded-2xl border border-primary/50 shadow-xl space-y-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-700/60">
              <div>
                <span className="text-xs uppercase tracking-wider text-primary font-bold">
                  Verified Analysis Report
                </span>
                <h3 className="text-2xl font-bold text-white mt-0.5">
                  {report.summary.target_name}
                </h3>
                <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-slate-400">
                  <span>
                    SKU Code: <strong className="text-slate-200 font-mono">{report.summary.sku}</strong>
                  </span>
                  <span>•</span>
                  <span>
                    Analysis Mode: <strong className="text-slate-200">{report.summary.mode}</strong>
                  </span>
                  <span>•</span>
                  <span>
                    Generated: <span className="font-mono">{report.summary.generated_at}</span>
                  </span>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleExportProfessionalReport}
                  disabled={isExportingReport}
                  className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/40 font-semibold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1.5 transition disabled:opacity-50"
                  title="Download professional category breakdown CSV"
                >
                  {isExportingReport ? (
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Download className="h-3.5 w-3.5" />
                  )}
                  <span>Export Professional Report (.csv)</span>
                </button>

                <Link
                  href={`/reports?mode=${mode}&selected_date=${selectedDate}&start_date=${startDate}&end_date=${endDate}&target_name=${encodeURIComponent(selectedSku === 'ALL' ? 'ALL' : (selectedSku || targetName))}`}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg text-xs flex items-center gap-1.5 transition"
                  title="View complete business audit & category breakdown in Reports Center"
                >
                  <span>Reports Center</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>

                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                  report.summary.is_forecast
                    ? 'bg-blue-500/20 text-blue-400 border-blue-500/40'
                    : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                }`}>
                  {report.summary.status}
                </span>

                <span className="bg-slate-800 text-slate-300 px-3 py-1 rounded-full text-xs font-mono border border-slate-700">
                  Model: {report.summary.model_used}
                </span>
              </div>
            </div>

            {/* Section B: Sales Performance Metrics Grid */}
            <div>
              <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">
                B. Sales Performance &amp; Revenue Telemetry
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                
                <div className="bg-background p-4 rounded-xl border border-slate-800 shadow-inner">
                  <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                    <span>Total Sales Revenue</span>
                    <DollarSign className="h-4 w-4 text-emerald-400" />
                  </div>
                  <div className="text-2xl font-extrabold text-white">
                    ${report.sales_performance.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Avg Unit Price: ${report.sales_performance.avg_unit_price.toFixed(2)}
                  </span>
                </div>

                <div className="bg-background p-4 rounded-xl border border-slate-800 shadow-inner">
                  <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                    <span>Quantity Sold</span>
                    <Package className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-extrabold text-white">
                    {report.sales_performance.total_units.toLocaleString()} units
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Observed in target timeframe
                  </span>
                </div>

                <div className="bg-background p-4 rounded-xl border border-slate-800 shadow-inner">
                  <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                    <span>Daily Sales Average</span>
                    <BarChart3 className="h-4 w-4 text-indigo-400" />
                  </div>
                  <div className="text-2xl font-extrabold text-white">
                    ${report.sales_performance.avg_daily_sales.toFixed(2)}
                    <span className="text-xs text-slate-400 font-normal"> /day</span>
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Based on calendar duration
                  </span>
                </div>

                <div className="bg-background p-4 rounded-xl border border-slate-800 shadow-inner">
                  <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                    <span>Period Comparison</span>
                    {report.sales_performance.growth_vs_prior_period_pct != null && report.sales_performance.growth_vs_prior_period_pct >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-emerald-400" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-danger" />
                    )}
                  </div>
                  <div className="text-2xl font-extrabold text-white">
                    {report.sales_performance.growth_vs_prior_period_pct != null ? (
                      <span className={report.sales_performance.growth_vs_prior_period_pct >= 0 ? 'text-emerald-400' : 'text-danger'}>
                        {report.sales_performance.growth_vs_prior_period_pct >= 0 ? '+' : ''}
                        {report.sales_performance.growth_vs_prior_period_pct}%
                      </span>
                    ) : (
                      <span className="text-slate-500 text-lg">N/A</span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    {report.sales_performance.prior_period_revenue != null
                      ? `Prior Period: $${report.sales_performance.prior_period_revenue.toLocaleString()}`
                      : 'Compared to equivalent historical cycle'}
                  </span>
                </div>

              </div>

              {/* Peak & Lowest Trading Days (when available) */}
              {report.sales_performance.highest_sales_date && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div className="bg-emerald-950/20 border border-emerald-500/30 p-3.5 rounded-xl flex items-center justify-between text-xs">
                    <div>
                      <span className="text-emerald-400 font-bold block">
                        Highest Sales Record ({report.sales_performance.highest_sales_date.date})
                      </span>
                      <span className="text-slate-300">
                        {report.sales_performance.highest_sales_date.units} units sold
                      </span>
                    </div>
                    <span className="text-base font-extrabold text-emerald-300 font-mono">
                      ${report.sales_performance.highest_sales_date.revenue.toFixed(2)}
                    </span>
                  </div>

                  {report.sales_performance.lowest_sales_date && (
                    <div className="bg-slate-900/40 border border-slate-700/60 p-3.5 rounded-xl flex items-center justify-between text-xs">
                      <div>
                        <span className="text-slate-400 font-medium block">
                          Lowest Active Record ({report.sales_performance.lowest_sales_date.date})
                        </span>
                        <span className="text-slate-400">
                          {report.sales_performance.lowest_sales_date.units} units sold
                        </span>
                      </div>
                      <span className="text-base font-extrabold text-slate-300 font-mono">
                        ${report.sales_performance.lowest_sales_date.revenue.toFixed(2)}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Section C: Forecast Results & Cross-Validation Metrics */}
            {report.forecast_results && (
              <div className="pt-4 border-t border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-primary" />
                    C. Forecast Modeling &amp; Walk-Forward Evaluation
                  </h4>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-400 font-mono">
                      Model: {report.forecast_results.model_name}
                    </span>
                    <Link
                      href="/model-health"
                      className="text-[11px] text-primary hover:underline font-medium inline-flex items-center gap-1"
                    >
                      <span>Model Health Telemetry</span>
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-background p-4 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400 block mb-1">
                      {report.summary.is_forecast ? 'Projected Demand Target' : 'Model Output Target'}
                    </span>
                    <div className="text-xl font-bold text-primary">
                      {report.forecast_results.predicted_units != null
                        ? `${report.forecast_results.predicted_units} units`
                        : `${report.sales_performance.total_units} units (Empirical Actual)`}
                    </div>
                    {report.forecast_results.lower_bound != null && report.forecast_results.upper_bound != null && (
                      <span className="text-[11px] text-slate-400 mt-1 block font-mono">
                        85% Conf. Interval: [{report.forecast_results.lower_bound} – {report.forecast_results.upper_bound}]
                      </span>
                    )}
                  </div>

                  <div className="bg-background p-4 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400 block mb-1">
                      Walk-Forward Test MAE
                    </span>
                    <div className="text-xl font-bold text-white font-mono">
                      {report.forecast_results.evaluation_metrics.mae ?? '0.00'}
                    </div>
                    <span className="text-[11px] text-slate-500 mt-1 block">
                      Mean Absolute Error on holdout
                    </span>
                  </div>

                  <div className="bg-background p-4 rounded-xl border border-slate-800">
                    <span className="text-xs text-slate-400 block mb-1">
                      Weighted Error Rate (WAPE)
                    </span>
                    <div className="text-xl font-bold text-white font-mono">
                      {report.forecast_results.evaluation_metrics.wape != null
                        ? `${report.forecast_results.evaluation_metrics.wape}%`
                        : 'N/A'}
                    </div>
                    <span className="text-[11px] text-emerald-400 mt-1 block">
                      {report.forecast_results.evaluation_metrics.wape != null &&
                      report.forecast_results.evaluation_metrics.wape <= 15
                        ? '✓ Within Enterprise Tolerance (≤15%)'
                        : 'Evaluated against snaive baseline'}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-400 italic">
                  Note: {report.forecast_results.explanation} {report.forecast_results.limitations}
                </p>
              </div>
            )}
          </div>

          {/* Section D: Interactive Time-Series Charts */}
          <div className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h4 className="text-lg font-bold text-white flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  D. Sales Trajectory &amp; Time-Series Visualization
                </h4>
                <p className="text-xs text-slate-400">
                  Emerald line represents actual recorded ledger sales; blue dashed line indicates forecasted trajectory.
                </p>
              </div>

              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" /> Actual Sales
                </span>
                <span className="flex items-center gap-1.5 text-blue-400 font-medium">
                  <span className="w-3 h-0.5 border-t-2 border-dashed border-blue-400 inline-block" /> Forecast
                </span>
                <span className="flex items-center gap-1.5 text-slate-400">
                  <span className="w-3 h-3 rounded bg-blue-500/20 inline-block" /> Confidence Band
                </span>
              </div>
            </div>

            <ForecastChart data={report.chart_data || []} />
          </div>

          {/* Section E: Business Insights & Strategy */}
          <div className="bg-surface p-6 rounded-2xl border border-slate-700 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h4 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-400" />
                E. Data-Grounded Business Insights &amp; Strategic Actions
              </h4>
              <Link
                href="/gemini"
                className="text-xs text-primary hover:text-blue-400 font-semibold flex items-center gap-1 transition"
              >
                <span>Consult Gemini Pro AI</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {report.insights.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-background p-4 rounded-xl border border-slate-800 space-y-1.5 hover:border-slate-700 transition"
                >
                  <div className="flex items-center gap-2">
                    {item.type === 'action' ? (
                      <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    ) : item.type === 'peak' ? (
                      <TrendingUp className="h-4 w-4 text-amber-400" />
                    ) : (
                      <Info className="h-4 w-4 text-primary" />
                    )}
                    <h5 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                      {item.title}
                    </h5>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Initial Empty State before User Analyzes */}
      {!report && !isAnalyzing && (
        <div className="bg-surface/50 border border-dashed border-slate-700 rounded-2xl p-12 text-center space-y-4">
          <div className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mx-auto shadow-inner">
            <BarChart3 className="h-8 w-8" />
          </div>
          <div className="max-w-md mx-auto">
            <h3 className="text-lg font-semibold text-white">Ready for Date Analysis</h3>
            <p className="text-xs text-slate-400 mt-1">
              Select your Target Product Name, choose either <strong>Option A (Selected Date)</strong> or <strong>Option B (Date Range)</strong>, and click <em>Analyse &amp; Generate Report</em> to run walk-forward cross-validation and review verified sales metrics.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
