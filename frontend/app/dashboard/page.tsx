'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import KPICard from '../../components/dashboard/KPICard'
import DataIngestionOverviewCard from '../../components/dashboard/DataIngestionOverviewCard'
import { useSalesData } from '../../hooks/useSalesData'
import {
  UploadCloud,
  ArrowRight,
  BarChart2,
  Calendar,
  DollarSign,
  ShoppingCart,
  Package,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  Percent,
  Layers,
  Activity
} from 'lucide-react'

// Dynamically import Recharts component with ssr: false to prevent SSR DOM measurement hangs
const ForecastChart = dynamic(() => import('../../components/charts/ForecastChart'), {
  ssr: false,
  loading: () => (
    <div className="h-80 w-full flex items-center justify-center text-slate-500">
      <p className="animate-pulse">Loading chart visualization...</p>
    </div>
  ),
})

const PERIOD_OPTIONS = [
  { value: 'all', label: 'All Time' },
  { value: 'today', label: 'Today (Latest Day)' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: 'this_month', label: 'This Month' },
  { value: 'last_month', label: 'Previous Month' },
  { value: 'custom', label: 'Custom Range' },
]

export default function DashboardOverview() {
  const [period, setPeriod] = useState<string>('all')
  const [customStart, setCustomStart] = useState<string>('')
  const [customEnd, setCustomEnd] = useState<string>('')

  const { data, isLoading, error, refetch } = useSalesData({
    period,
    startDate: period === 'custom' ? customStart : undefined,
    endDate: period === 'custom' ? customEnd : undefined,
  })

  const overview = data?.overview
  const totalRecords = overview?.total_records ?? 0
  const revenue = overview?.revenue ?? 0
  const activePredictions = overview?.active_predictions ?? 0
  const hasData = Boolean(
    overview && (totalRecords > 0 || revenue > 0 || activePredictions > 0)
  )

  const revenueGrowth = overview?.revenue_growth
  const growthTrend = revenueGrowth != null
    ? `${revenueGrowth >= 0 ? '+' : ''}${revenueGrowth}%`
    : undefined

  const totalOrders = overview?.total_orders ?? 0
  const totalQuantity = overview?.total_quantity ?? 0
  const aov = overview?.aov ?? 0
  const totalProfit = overview?.total_profit
  const profitMargin = overview?.profit_margin_pct
  const forecastedRevenue = overview?.forecasted_revenue ?? 0
  const anomaliesCount = overview?.anomalies_detected ?? 0

  const modelAccuracy = overview?.model_accuracy != null
    ? `${overview.model_accuracy}%`
    : '--'

  const forecastPoints = Array.isArray(data?.forecast) ? data.forecast : []
  const hasForecast = forecastPoints.length > 0
  const insights = overview?.insights ?? []

  return (
    <div className="space-y-6">
      {/* Header with Title and Period Filter */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Global Sales Overview</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Enterprise sales intelligence, forecasting telemetry, and executive performance metrics.
          </p>
        </div>

        {/* Period Selector Bar */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex rounded-lg bg-slate-800/90 p-1 border border-slate-700/80">
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setPeriod(opt.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition ${
                  period === opt.value
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                {opt.label}
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
                placeholder="Start"
              />
              <span className="text-slate-500">to</span>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="bg-transparent text-white focus:outline-none text-xs"
                placeholder="End"
              />
            </div>
          )}

          {isLoading && (
            <span className="text-xs bg-slate-800 text-primary border border-primary/30 px-3 py-1.5 rounded-lg animate-pulse">
              Syncing...
            </span>
          )}
        </div>
      </header>

      {/* Top Data Ingestion & Live Dataset Preview Section */}
      <DataIngestionOverviewCard onDataUploaded={() => refetch()} />

      {/* Date Range & Comparison Banner */}
      {overview?.date_range && (
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 bg-slate-900/60 px-4 py-2.5 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>
              Active Window: <strong className="text-white">{overview.date_range.start_date}</strong> to <strong className="text-white">{overview.date_range.end_date}</strong>
            </span>
          </div>
          {overview.comparison_range && (
            <div className="text-slate-400">
              Prior Cycle Comparison: {overview.comparison_range.start_date} to {overview.comparison_range.end_date}
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="p-4 bg-danger/10 border border-danger/40 text-danger rounded-xl text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>Failed to sync with backend API. Ensure the backend server is running on port 8000.</span>
        </div>
      )}

      {/* Empty State Banner when no dataset has been imported */}
      {!isLoading && !hasData && (
        <div className="bg-surface/90 border border-dashed border-slate-700 rounded-2xl p-8 sm:p-12 text-center flex flex-col items-center justify-center space-y-4 shadow-xl">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
            <UploadCloud className="w-8 h-8" />
          </div>
          <div className="max-w-md">
            <h3 className="text-xl font-bold text-white mb-2">Please import a dataset to view analytics</h3>
            <p className="text-sm text-slate-400">
              No sales transactions have been loaded yet. Upload your store sales CSV in Data Ingestion to calculate real revenue, track SKUs, generate forecast trajectories, and detect anomalies.
            </p>
          </div>
          <Link 
            href="/data" 
            className="inline-flex items-center gap-2 bg-primary hover:bg-blue-600 text-white font-medium px-5 py-2.5 rounded-xl shadow-md transition"
          >
            Import Sales Dataset <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Primary KPI Grid (10 Core SaaS Metrics) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard 
          title="Total Sales / Revenue" 
          value={
            isLoading
              ? 'Loading...'
              : `$${(revenue || 0).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`
          } 
          trend={growthTrend}
          subtitle={revenueGrowth != null ? `vs prior ${period} cycle` : 'Store-wide gross sales'}
          tooltip="Gross revenue calculated from line-item transactions (total_sales or units_sold * price)."
          icon={<DollarSign className="w-4 h-4" />}
        />

        <KPICard 
          title="Distinct Orders" 
          value={isLoading ? 'Loading...' : totalOrders.toLocaleString()} 
          subtitle="Unique transaction IDs"
          tooltip="Calculated using verified COUNT(DISTINCT order_id) across historical sales orders."
          icon={<ShoppingCart className="w-4 h-4" />}
        />

        <KPICard 
          title="Total Quantity Sold" 
          value={isLoading ? 'Loading...' : totalQuantity.toLocaleString()} 
          subtitle="Physical units fulfilled"
          tooltip="Sum of units_sold across all valid transaction rows in the selected period."
          icon={<Package className="w-4 h-4" />}
        />

        <KPICard 
          title="Average Order Value (AOV)" 
          value={isLoading ? 'Loading...' : `$${aov.toFixed(2)}`} 
          subtitle="Revenue per distinct order"
          tooltip="Total period revenue divided by distinct orders (never double-counted)."
          icon={<TrendingUp className="w-4 h-4" />}
        />

        <KPICard 
          title="Total Profit" 
          value={
            isLoading
              ? 'Loading...'
              : totalProfit !== null && totalProfit !== undefined
              ? `${totalProfit < 0 ? '-' : ''}$${Math.abs(totalProfit).toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}`
              : 'N/A'
          }
          isDanger={totalProfit !== null && totalProfit !== undefined && totalProfit < 0}
          subtitle={
            totalProfit !== null && totalProfit !== undefined
              ? (totalProfit >= 0 ? 'Operating commercial gain' : 'Commercial net loss')
              : 'Profit column absent in source dataset'
          }
          tooltip="Sum of commercial profit. Preserves actual negative margins and loss-making sales."
        />

        <KPICard 
          title="Operating Profit Margin" 
          value={
            isLoading
              ? 'Loading...'
              : profitMargin !== null && profitMargin !== undefined
              ? `${profitMargin}%`
              : 'N/A'
          } 
          isDanger={profitMargin !== null && profitMargin !== undefined && profitMargin < 0}
          subtitle="Profit / Revenue percentage"
          tooltip="Net commercial margin. Outputs N/A if profit field is omitted from dataset schema."
          icon={<Percent className="w-4 h-4" />}
        />

        <KPICard 
          title="Forecasted Revenue (7d)" 
          value={isLoading ? 'Loading...' : `$${forecastedRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} 
          subtitle="Run-rate demand projection"
          tooltip="Estimated forward commercial revenue based on current velocity and ML forecast."
          icon={<Activity className="w-4 h-4" />}
        />

        <KPICard 
          title="Active Products / SKUs" 
          value={isLoading ? 'Loading...' : `${activePredictions || 0} Products`} 
          subtitle="Tracked in catalog"
          tooltip="Unique product codes with historical transaction recordings."
          icon={<Layers className="w-4 h-4" />}
        />
      </div>

      {/* Secondary Status Row: Accuracy & Anomalies */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-surface p-5 rounded-xl border border-slate-700/80 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium block">Forecasting Evaluation (WAPE)</span>
            <span className="text-2xl font-bold text-white mt-1 block">
              {isLoading ? '...' : modelAccuracy}
            </span>
            <p className="text-xs text-slate-400 mt-1">
              Rolling walk-forward cross-validation accuracy on test partition.
            </p>
          </div>
          <Link
            href="/model-health"
            className="text-xs text-primary font-semibold hover:underline border border-primary/20 bg-primary/10 px-3 py-1.5 rounded-lg"
          >
            Model Health &rarr;
          </Link>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-slate-700/80 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium block">Anomaly Alerts in Period</span>
            <span className={`text-2xl font-bold mt-1 block ${anomaliesCount > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
              {isLoading ? '...' : `${anomaliesCount} Detected`}
            </span>
            <p className="text-xs text-slate-400 mt-1">
              {anomaliesCount > 0 ? 'Statistical demand spikes/drops flagged for review.' : 'All SKU demand trajectories within 2.5-sigma bounds.'}
            </p>
          </div>
          <Link
            href="/anomalies"
            className="text-xs text-amber-400 font-semibold hover:underline border border-amber-500/20 bg-amber-500/10 px-3 py-1.5 rounded-lg"
          >
            Review Anomalies &rarr;
          </Link>
        </div>
      </div>

      {/* Business Insights Callout */}
      {insights.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-4 h-4 text-amber-400" />
            <h4 className="text-sm font-semibold text-white">Empirical Business Insights & Diagnostics</h4>
          </div>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-300">
            {insights.map((ins: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2 bg-surface/60 p-2.5 rounded-lg border border-slate-800">
                <span className="text-primary font-bold">&bull;</span>
                <span>{ins}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Main Chart */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-white">Actual vs Forecast (Confidence Bounds)</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Historical units sold compared with 7-day walk-forward projections and 85–115% uncertainty bounds.
            </p>
          </div>
          <Link href="/forecast" className="text-xs text-primary font-semibold hover:underline">
            Open Forecast Lab &rarr;
          </Link>
        </div>

        {hasForecast ? (
          <ForecastChart data={forecastPoints} />
        ) : (
          <div className="h-64 w-full flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl p-6 text-center text-slate-500">
            <BarChart2 className="w-10 h-10 mb-2 opacity-40 text-slate-400" />
            <p className="font-medium text-slate-400">No forecast trajectory available</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              {hasData 
                ? 'Generate forecasts by selecting a product or date range in the Forecast Lab.' 
                : 'Please import a dataset to view actual vs. forecast confidence bounds.'}
            </p>
          </div>
        )}
      </div>

      {/* Quick Action Navigation Cards (7 Modules) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <Link href="/analytics" className="bg-surface hover:border-primary p-5 rounded-xl border border-slate-700 transition flex flex-col justify-between group">
          <div>
            <h4 className="text-white font-semibold group-hover:text-primary transition flex items-center justify-between">
              Sales Analytics <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition" />
            </h4>
            <p className="text-xs text-slate-400 mt-1">Deep-dive trends, category/sub-category contribution, product rankings, and line-item explorer.</p>
          </div>
          <span className="text-xs text-primary font-bold mt-4 block">Explore Sales Analytics &rarr;</span>
        </Link>

        <Link href="/forecast" className="bg-surface hover:border-primary p-5 rounded-xl border border-slate-700 transition flex flex-col justify-between group">
          <div>
            <h4 className="text-white font-semibold group-hover:text-primary transition flex items-center justify-between">
              Forecast Lab <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition" />
            </h4>
            <p className="text-xs text-slate-400 mt-1">Single Date (Option A) vs Date Range (Option B), walk-forward validation (snaive vs ARIMA), and MAE/WAPE.</p>
          </div>
          <span className="text-xs text-primary font-bold mt-4 block">Launch Forecast Lab &rarr;</span>
        </Link>

        <Link href="/gemini" className="bg-surface hover:border-primary p-5 rounded-xl border border-slate-700 transition flex flex-col justify-between group">
          <div>
            <h4 className="text-white font-semibold group-hover:text-primary transition flex items-center justify-between">
              Gemini Pro AI Advisor <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition" />
            </h4>
            <p className="text-xs text-slate-400 mt-1">Natural language sales advisor grounded in deterministic revenue, stock risks, and anomaly facts.</p>
          </div>
          <span className="text-xs text-primary font-bold mt-4 block">Consult Gemini Pro &rarr;</span>
        </Link>

        <Link href="/anomalies" className="bg-surface hover:border-primary p-5 rounded-xl border border-slate-700 transition flex flex-col justify-between group">
          <div>
            <h4 className="text-white font-semibold group-hover:text-primary transition flex items-center justify-between">
              Anomaly Detection <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition" />
            </h4>
            <p className="text-xs text-slate-400 mt-1">Dynamic rolling Z-score detection with severity markers (Critical/Warning) and root cause guidance.</p>
          </div>
          <span className="text-xs text-primary font-bold mt-4 block">View Anomaly Register &rarr;</span>
        </Link>

        <Link href="/reports" className="bg-surface hover:border-primary p-5 rounded-xl border border-slate-700 transition flex flex-col justify-between group">
          <div>
            <h4 className="text-white font-semibold group-hover:text-primary transition flex items-center justify-between">
              Reports & Exports <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition" />
            </h4>
            <p className="text-xs text-slate-400 mt-1">Export professional_sales_summary_YYYY-MM-DD.csv with verified Category and Sub-Category breakdowns.</p>
          </div>
          <span className="text-xs text-primary font-bold mt-4 block">Export Reports &rarr;</span>
        </Link>

        <Link href="/data" className="bg-surface hover:border-primary p-5 rounded-xl border border-slate-700 transition flex flex-col justify-between group">
          <div>
            <h4 className="text-white font-semibold group-hover:text-primary transition flex items-center justify-between">
              Data Ingestion & Preview <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition" />
            </h4>
            <p className="text-xs text-slate-400 mt-1">Drag-and-drop CSV upload, schema preview, missing value analysis, and safe database reset.</p>
          </div>
          <span className="text-xs text-primary font-bold mt-4 block">Manage Datasets &rarr;</span>
        </Link>
      </div>
    </div>
  )
}
