'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import api from '../../lib/api'
import {
  TrendingUp,
  Layers,
  ShoppingBag,
  ListFilter,
  Search,
  ArrowUpDown,
  Calendar,
  DollarSign,
  Package,
  ShoppingCart,
  ChevronLeft,
  ChevronRight,
  Download,
  UploadCloud,
  ArrowRight
} from 'lucide-react'

// Dynamic import for Recharts component to avoid SSR hydration mismatches
const TrendsChart = dynamic(() => import('../../components/charts/TrendsChart'), {
  ssr: false,
  loading: () => (
    <div className="h-72 w-full flex items-center justify-center text-slate-500">
      <p className="animate-pulse">Loading trend visualization...</p>
    </div>
  ),
})

type TabType = 'trends' | 'categories' | 'products' | 'transactions'

export default function SalesAnalyticsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('trends')
  const [period, setPeriod] = useState<string>('all')
  const [interval, setInterval] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [customStart, setCustomStart] = useState<string>('')
  const [customEnd, setCustomEnd] = useState<string>('')

  // Trends state
  const [trendsData, setTrendsData] = useState<any>(null)
  const [loadingTrends, setLoadingTrends] = useState<boolean>(false)

  // Categories state
  const [categoriesData, setCategoriesData] = useState<any>(null)
  const [loadingCategories, setLoadingCategories] = useState<boolean>(false)

  // Products state
  const [productsData, setProductsData] = useState<any>(null)
  const [productSearch, setProductSearch] = useState<string>('')
  const [loadingProducts, setLoadingProducts] = useState<boolean>(false)

  // Transactions state
  const [transactionsData, setTransactionsData] = useState<any>(null)
  const [transPage, setTransPage] = useState<number>(1)
  const [transSearch, setTransSearch] = useState<string>('')
  const [transCategory, setTransCategory] = useState<string>('ALL')
  const [transSortBy, setTransSortBy] = useState<string>('date')
  const [transSortDir, setTransSortDir] = useState<'asc' | 'desc'>('desc')
  const [loadingTrans, setLoadingTrans] = useState<boolean>(false)

  // Fetch Trends
  const fetchTrends = async () => {
    setLoadingTrends(true)
    try {
      const params: any = { interval, period }
      if (period === 'custom' && customStart) params.start_date = customStart
      if (period === 'custom' && customEnd) params.end_date = customEnd
      const res = await api.get('/api/v1/analytics/trends', { params })
      setTrendsData(res.data)
    } catch (err) {
      console.error('Failed to fetch trends:', err)
    } finally {
      setLoadingTrends(false)
    }
  }

  // Fetch Categories
  const fetchCategories = async () => {
    setLoadingCategories(true)
    try {
      const params: any = { period }
      if (period === 'custom' && customStart) params.start_date = customStart
      if (period === 'custom' && customEnd) params.end_date = customEnd
      const res = await api.get('/api/v1/analytics/categories', { params })
      setCategoriesData(res.data)
    } catch (err) {
      console.error('Failed to fetch categories:', err)
    } finally {
      setLoadingCategories(false)
    }
  }

  // Fetch Products
  const fetchProducts = async () => {
    setLoadingProducts(true)
    try {
      const params: any = { period, limit: 10 }
      if (productSearch) params.search = productSearch
      if (period === 'custom' && customStart) params.start_date = customStart
      if (period === 'custom' && customEnd) params.end_date = customEnd
      const res = await api.get('/api/v1/analytics/products', { params })
      setProductsData(res.data)
    } catch (err) {
      console.error('Failed to fetch products:', err)
    } finally {
      setLoadingProducts(false)
    }
  }

  // Fetch Transactions
  const fetchTransactions = async () => {
    setLoadingTrans(true)
    try {
      const params: any = {
        page: transPage,
        page_size: 20,
        sort_by: transSortBy,
        sort_dir: transSortDir,
      }
      if (transSearch) params.search = transSearch
      if (transCategory && transCategory !== 'ALL') params.category = transCategory
      if (period === 'custom' && customStart) params.start_date = customStart
      if (period === 'custom' && customEnd) params.end_date = customEnd
      const res = await api.get('/api/v1/analytics/transactions', { params })
      setTransactionsData(res.data)
    } catch (err) {
      console.error('Failed to fetch transactions:', err)
    } finally {
      setLoadingTrans(false)
    }
  }

  // Trigger loads based on active tab
  useEffect(() => {
    if (activeTab === 'trends') fetchTrends()
    if (activeTab === 'categories') fetchCategories()
    if (activeTab === 'products') fetchProducts()
    if (activeTab === 'transactions') fetchTransactions()
  }, [activeTab, period, interval])

  useEffect(() => {
    if (activeTab === 'transactions') fetchTransactions()
  }, [transPage, transSortBy, transSortDir, transCategory])

  const handleTransSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setTransPage(1)
    fetchTransactions()
  }

  const handleProductSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchProducts()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Sales Analytics</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Deep-dive multi-dimensional performance intelligence, category contributions, and line-item audits.
          </p>
        </div>

        {/* Global Period Filter */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex rounded-lg bg-slate-800/90 p-1 border border-slate-700/80">
            {['all', 'today', '7d', '30d', 'this_month', 'last_month', 'custom'].map((opt) => (
              <button
                key={opt}
                onClick={() => setPeriod(opt)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${
                  period === opt
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                {opt === 'all'
                  ? 'All Time'
                  : opt === 'today'
                  ? 'Today'
                  : opt === '7d'
                  ? '7 Days'
                  : opt === '30d'
                  ? '30 Days'
                  : opt === 'this_month'
                  ? 'This Month'
                  : opt === 'last_month'
                  ? 'Last Month'
                  : 'Custom'}
              </button>
            ))}
          </div>

          {period === 'custom' && (
            <div className="flex items-center gap-2 bg-surface px-3 py-1.5 rounded-lg border border-slate-700 text-xs">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                className="bg-transparent text-white focus:outline-none text-xs"
              />
              <span className="text-slate-500">to</span>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="bg-transparent text-white focus:outline-none text-xs"
              />
              <button
                onClick={() => {
                  if (activeTab === 'trends') fetchTrends()
                  if (activeTab === 'categories') fetchCategories()
                  if (activeTab === 'products') fetchProducts()
                  if (activeTab === 'transactions') fetchTransactions()
                }}
                className="bg-primary/20 text-primary px-2 py-0.5 rounded text-xs hover:bg-primary/30"
              >
                Apply
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Module Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-1">
        <button
          onClick={() => setActiveTab('trends')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
            activeTab === 'trends'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Time-Series Trends
        </button>

        <button
          onClick={() => setActiveTab('categories')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
            activeTab === 'categories'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <Layers className="w-4 h-4" />
          Categories & Sub-Categories
        </button>

        <button
          onClick={() => setActiveTab('products')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
            activeTab === 'products'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <ShoppingBag className="w-4 h-4" />
          Product Rankings
        </button>

        <button
          onClick={() => setActiveTab('transactions')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
            activeTab === 'transactions'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <ListFilter className="w-4 h-4" />
          Transaction Explorer
        </button>
      </div>

      {/* TAB 1: TIME-SERIES TRENDS */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 bg-surface p-4 rounded-xl border border-slate-700">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Aggregation Interval:</span>
              <div className="inline-flex rounded-lg bg-slate-800 p-0.5 border border-slate-700">
                {(['daily', 'weekly', 'monthly'] as const).map((intVal) => (
                  <button
                    key={intVal}
                    onClick={() => setInterval(intVal)}
                    className={`px-3 py-1 text-xs font-medium rounded-md capitalize transition ${
                      interval === intVal ? 'bg-primary text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {intVal}
                  </button>
                ))}
              </div>
            </div>

            {trendsData && (
              <div className="flex items-center gap-4 text-xs">
                {trendsData.peak_date && (
                  <div className="bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg text-emerald-400">
                    Peak Sales: <strong className="text-white">{trendsData.peak_date}</strong> (${trendsData.peak_revenue?.toLocaleString()})
                  </div>
                )}
                {trendsData.lowest_date && (
                  <div className="bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-lg text-rose-400">
                    Trough: <strong className="text-white">{trendsData.lowest_date}</strong> (${trendsData.lowest_revenue?.toLocaleString()})
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Main Chart */}
          <div className="bg-surface p-6 rounded-xl border border-slate-700">
            <h3 className="text-base font-semibold text-white mb-1">Revenue ($) & Units Sold Trajectory</h3>
            <p className="text-xs text-slate-400 mb-4">
              Bars indicate gross line revenue; purple line traces fulfilled physical quantity over the chosen interval.
            </p>
            {loadingTrends ? (
              <div className="h-72 w-full flex items-center justify-center text-slate-500">
                <p className="animate-pulse">Loading trend points...</p>
              </div>
            ) : trendsData?.series?.length > 0 ? (
              <TrendsChart data={trendsData.series} metric="both" />
            ) : (
              <div className="h-64 w-full flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl p-6 text-center text-slate-500">
                <p>No trend data available. Please upload a sales dataset in Data Ingestion.</p>
              </div>
            )}
          </div>

          {/* Period Table View */}
          {trendsData?.series?.length > 0 && (
            <div className="bg-surface rounded-xl border border-slate-700 overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white">Aggregated Interval Breakdown</h4>
                <span className="text-xs text-slate-400">{trendsData.series.length} periods evaluated</span>
              </div>
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-300 sticky top-0 border-b border-slate-700">
                    <tr>
                      <th className="py-2.5 px-4 font-semibold">Period Date</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Revenue ($)</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Units Sold</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Distinct Orders</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Profit ($)</th>
                      <th className="py-2.5 px-4 font-semibold text-right">Delta (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {trendsData.series.map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-4 font-mono text-slate-300">{row.date}</td>
                        <td className="py-2.5 px-4 text-right font-medium text-white">
                          ${row.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-4 text-right text-slate-300">{row.units_sold.toLocaleString()}</td>
                        <td className="py-2.5 px-4 text-right text-slate-300">{row.orders.toLocaleString()}</td>
                        <td className="py-2.5 px-4 text-right">
                          {row.profit !== null && row.profit !== undefined ? (
                            <span className={row.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                              {row.profit < 0 ? '-' : ''}${Math.abs(row.profit).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          {row.growth_delta_pct !== null && row.growth_delta_pct !== undefined ? (
                            <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                              row.growth_delta_pct >= 0 ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                            }`}>
                              {row.growth_delta_pct >= 0 ? '+' : ''}{row.growth_delta_pct}%
                            </span>
                          ) : (
                            <span className="text-slate-500">--</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CATEGORY & SUB-CATEGORY BREAKDOWN */}
      {activeTab === 'categories' && (
        <div className="space-y-6">
          {/* Highlights Header */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-surface p-5 rounded-xl border border-slate-700">
              <span className="text-xs text-slate-400 font-medium block">Total Store Sales (Period)</span>
              <span className="text-2xl font-bold text-white mt-1 block">
                ${categoriesData?.total_store_revenue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </span>
              <p className="text-xs text-slate-400 mt-1">Summed across all categories</p>
            </div>

            <div className="bg-surface p-5 rounded-xl border border-slate-700">
              <span className="text-xs text-slate-400 font-medium block">Top Performing Category</span>
              <span className="text-2xl font-bold text-emerald-400 mt-1 block">
                {categoriesData?.best_category || 'N/A'}
              </span>
              <p className="text-xs text-slate-400 mt-1">Highest gross revenue contribution</p>
            </div>

            <div className="bg-surface p-5 rounded-xl border border-slate-700">
              <span className="text-xs text-slate-400 font-medium block">Lowest Performing Category</span>
              <span className="text-2xl font-bold text-amber-400 mt-1 block">
                {categoriesData?.lowest_category || 'N/A'}
              </span>
              <p className="text-xs text-slate-400 mt-1">Opportunity for promotional lift</p>
            </div>
          </div>

          {/* Category Contribution Progress Cards */}
          {categoriesData?.category_summary && (
            <div className="bg-surface p-6 rounded-xl border border-slate-700">
              <h3 className="text-base font-semibold text-white mb-4">Category Revenue Contribution %</h3>
              <div className="space-y-4">
                {categoriesData.category_summary.map((cat: any, idx: number) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-white">{cat.category}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-slate-400">
                          ${cat.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                        <span className="font-mono font-bold text-primary">{cat.contribution_pct}%</span>
                      </div>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-primary h-2 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, Math.max(1, cat.contribution_pct))}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detailed Sub-Category Table */}
          <div className="bg-surface rounded-xl border border-slate-700 overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-white">Category & Sub-Category Detailed Ledger</h4>
                <p className="text-xs text-slate-400 mt-0.5">Calculates distinct orders, physical volume, revenue, profit, and margin.</p>
              </div>
              <Link
                href="/reports"
                className="inline-flex items-center gap-1.5 text-xs text-primary border border-primary/30 bg-primary/10 px-3 py-1.5 rounded-lg hover:bg-primary/20 transition"
              >
                <Download className="w-3.5 h-3.5" /> Export Official CSV
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/80 text-slate-300 border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">Category</th>
                    <th className="py-2.5 px-4 font-semibold">Sub-Category</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Orders</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Units</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Revenue ($)</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Profit ($)</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Margin (%)</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Share (%)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loadingCategories ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500 animate-pulse">
                        Calculating category breakdown...
                      </td>
                    </tr>
                  ) : categoriesData?.breakdown?.length > 0 ? (
                    categoriesData.breakdown.map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-4 font-medium text-white">{row.category}</td>
                        <td className="py-2.5 px-4 text-slate-300">{row.sub_category}</td>
                        <td className="py-2.5 px-4 text-right text-slate-300">{row.orders.toLocaleString()}</td>
                        <td className="py-2.5 px-4 text-right text-slate-300">{row.units_sold.toLocaleString()}</td>
                        <td className="py-2.5 px-4 text-right font-medium text-white">
                          ${row.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          {row.profit !== null && row.profit !== undefined ? (
                            <span className={row.profit >= 0 ? 'text-emerald-400' : 'text-rose-400 font-semibold'}>
                              {row.profit < 0 ? '-' : ''}${Math.abs(row.profit).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="py-2.5 px-4 text-right">
                          {row.profit_margin_pct !== null && row.profit_margin_pct !== undefined ? (
                            <span className={row.profit_margin_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                              {row.profit_margin_pct}%
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="py-2.5 px-4 text-right font-mono text-primary font-semibold">
                          {row.contribution_pct}%
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500">
                        No category data available for the selected period.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: PRODUCT PERFORMANCE */}
      {activeTab === 'products' && (
        <div className="space-y-6">
          {/* Search Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface p-4 rounded-xl border border-slate-700">
            <div>
              <h3 className="text-sm font-semibold text-white">Top & Lowest Performing Products</h3>
              <p className="text-xs text-slate-400 mt-0.5">Ranked by gross sales volume and commercial contribution %.</p>
            </div>
            <form onSubmit={handleProductSearchSubmit} className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Filter by product name or SKU..."
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  className="bg-slate-800 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-primary w-64"
                />
              </div>
              <button
                type="submit"
                className="bg-primary text-white text-xs px-3 py-1.5 rounded-lg hover:bg-blue-600 transition"
              >
                Search
              </button>
            </form>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top-Selling Products */}
            <div className="bg-surface rounded-xl border border-slate-700 overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-emerald-500/5">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <h4 className="text-sm font-semibold text-white">Top-Selling Products (by Revenue)</h4>
                </div>
                <span className="text-[11px] text-emerald-400 font-mono">Leaders</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-300 border-b border-slate-700">
                    <tr>
                      <th className="py-2.5 px-3">Product Name</th>
                      <th className="py-2.5 px-3 text-right">Units</th>
                      <th className="py-2.5 px-3 text-right">Revenue ($)</th>
                      <th className="py-2.5 px-3 text-right">Share (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {loadingProducts ? (
                      <tr><td colSpan={4} className="py-6 text-center text-slate-500 animate-pulse">Loading rankings...</td></tr>
                    ) : productsData?.top_selling?.length > 0 ? (
                      productsData.top_selling.map((p: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-800/40 transition">
                          <td className="py-2.5 px-3">
                            <span className="font-medium text-white block truncate max-w-[200px]" title={p.product_name}>
                              {p.product_name}
                            </span>
                            <span className="text-[10px] text-slate-500 font-mono block">SKU: {p.sku} &bull; {p.category}</span>
                          </td>
                          <td className="py-2.5 px-3 text-right text-slate-300">{p.units_sold.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-right font-medium text-white">
                            ${p.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono font-semibold text-emerald-400">
                            {p.contribution_pct}%
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr><td colSpan={4} className="py-6 text-center text-slate-500">No product records found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Lowest-Selling Products */}
            <div className="bg-surface rounded-xl border border-slate-700 overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-amber-500/5">
                <div className="flex items-center gap-2">
                  <ShoppingBag className="w-4 h-4 text-amber-400" />
                  <h4 className="text-sm font-semibold text-white">Lowest-Selling Products (Review Needed)</h4>
                </div>
                <span className="text-[11px] text-amber-400 font-mono">Troughs</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/80 text-slate-300 border-b border-slate-700">
                    <tr>
                      <th className="py-2.5 px-3">Product Name</th>
                      <th className="py-2.5 px-3 text-right">Units</th>
                      <th className="py-2.5 px-3 text-right">Revenue ($)</th>
                      <th className="py-2.5 px-3 text-right">Share (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {loadingProducts ? (
                      <tr><td colSpan={4} className="py-6 text-center text-slate-500 animate-pulse">Loading rankings...</td></tr>
                    ) : productsData?.lowest_selling?.length > 0 ? (
                      productsData.lowest_selling.map((p: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-800/40 transition">
                          <td className="py-2.5 px-3">
                            <span className="font-medium text-white block truncate max-w-[200px]" title={p.product_name}>
                              {p.product_name}
                            </span>
                            <span className="text-[10px] text-slate-500 font-mono block">SKU: {p.sku} &bull; {p.category}</span>
                          </td>
                          <td className="py-2.5 px-3 text-right text-slate-300">{p.units_sold.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-right font-medium text-white">
                            ${p.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="py-2.5 px-3 text-right font-mono font-semibold text-amber-400">
                            {p.contribution_pct}%
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr><td colSpan={4} className="py-6 text-center text-slate-500">No product records found.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: TRANSACTION EXPLORER */}
      {activeTab === 'transactions' && (
        <div className="space-y-4">
          {/* Controls Bar */}
          <div className="bg-surface p-4 rounded-xl border border-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-3">
            <form onSubmit={handleTransSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search by Order ID, SKU, Product Name..."
                  value={transSearch}
                  onChange={(e) => setTransSearch(e.target.value)}
                  className="bg-slate-800 text-xs text-white pl-8 pr-3 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-primary w-full"
                />
              </div>
              <button
                type="submit"
                className="bg-primary text-white text-xs px-3 py-1.5 rounded-lg hover:bg-blue-600 transition"
              >
                Filter
              </button>
            </form>

            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="text-slate-400">Sort By:</span>
                <select
                  value={transSortBy}
                  onChange={(e) => setTransSortBy(e.target.value)}
                  className="bg-slate-800 border border-slate-700 text-white rounded-lg px-2.5 py-1 text-xs focus:outline-none"
                >
                  <option value="date">Date</option>
                  <option value="order_id">Order ID</option>
                  <option value="total_sales">Revenue</option>
                  <option value="units_sold">Units</option>
                  <option value="profit">Profit</option>
                </select>
                <button
                  onClick={() => setTransSortDir(transSortDir === 'desc' ? 'asc' : 'desc')}
                  className="bg-slate-800 p-1.5 rounded-lg border border-slate-700 hover:text-white text-slate-300"
                  title="Toggle Ascending/Descending"
                >
                  <ArrowUpDown className="w-3.5 h-3.5" />
                </button>
              </div>

              {transactionsData && (
                <span className="text-slate-400 font-mono">
                  {transactionsData.total_count?.toLocaleString()} Records
                </span>
              )}
            </div>
          </div>

          {/* Interactive Transactions Table */}
          <div className="bg-surface rounded-xl border border-slate-700 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-800/90 text-slate-300 border-b border-slate-700">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">Date</th>
                    <th className="py-2.5 px-3 font-semibold">Order ID</th>
                    <th className="py-2.5 px-3 font-semibold">Product Name & SKU</th>
                    <th className="py-2.5 px-3 font-semibold">Category</th>
                    <th className="py-2.5 px-3 text-right font-semibold">Units</th>
                    <th className="py-2.5 px-3 text-right font-semibold">Price ($)</th>
                    <th className="py-2.5 px-3 text-right font-semibold">Total ($)</th>
                    <th className="py-2.5 px-3 text-right font-semibold">Profit ($)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loadingTrans ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-500 animate-pulse">
                        Querying transactions ledger...
                      </td>
                    </tr>
                  ) : transactionsData?.items?.length > 0 ? (
                    transactionsData.items.map((t: any) => (
                      <tr key={t.id} className="hover:bg-slate-800/40 transition">
                        <td className="py-2 px-3 font-mono text-slate-300 whitespace-nowrap">{t.date}</td>
                        <td className="py-2 px-3 font-mono font-medium text-primary whitespace-nowrap">{t.order_id}</td>
                        <td className="py-2 px-3">
                          <span className="font-medium text-white block truncate max-w-[240px]" title={t.product_name}>
                            {t.product_name}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">SKU: {t.sku}</span>
                        </td>
                        <td className="py-2 px-3 text-slate-400 whitespace-nowrap">
                          {t.category} <span className="text-slate-600">&rsaquo;</span> {t.sub_category}
                        </td>
                        <td className="py-2 px-3 text-right font-mono text-slate-200">{t.units_sold}</td>
                        <td className="py-2 px-3 text-right font-mono text-slate-400">
                          {t.price != null ? `$${t.price.toFixed(2)}` : 'N/A'}
                        </td>
                        <td className="py-2 px-3 text-right font-mono font-semibold text-white whitespace-nowrap">
                          ${t.total_sales.toFixed(2)}
                        </td>
                        <td className="py-2 px-3 text-right font-mono whitespace-nowrap">
                          {t.profit != null ? (
                            <span className={t.profit >= 0 ? 'text-emerald-400' : 'text-rose-400 font-semibold'}>
                              {t.profit < 0 ? '-' : ''}${Math.abs(t.profit).toFixed(2)}
                            </span>
                          ) : (
                            <span className="text-slate-500">N/A</span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-500">
                        No transactions found matching the filter criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {transactionsData && transactionsData.total_pages > 1 && (
              <div className="p-3 border-t border-slate-800 flex items-center justify-between text-xs bg-slate-850">
                <span className="text-slate-400">
                  Page <strong className="text-white">{transactionsData.page}</strong> of{' '}
                  <strong className="text-white">{transactionsData.total_pages}</strong>
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setTransPage(Math.max(1, transPage - 1))}
                    disabled={transPage <= 1 || loadingTrans}
                    className="p-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40 transition"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setTransPage(Math.min(transactionsData.total_pages, transPage + 1))}
                    disabled={transPage >= transactionsData.total_pages || loadingTrans}
                    className="p-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40 transition"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

