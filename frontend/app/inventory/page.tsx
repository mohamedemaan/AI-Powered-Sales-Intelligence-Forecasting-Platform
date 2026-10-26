'use client'

import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'

export default function InventoryPage() {
  const { data: inventoryItems, isLoading, error, refetch } = useQuery({
    queryKey: ['inventory-intelligence'],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/inventory')
      return res.data
    }
  })

  const hasInventoryTracking = inventoryItems && inventoryItems.length > 0 && inventoryItems.some((item: any) => item.has_inventory_tracking === true)
  const criticalCount = inventoryItems?.filter((item: any) => item.health_status === 'CRITICAL').length || 0
  const warningCount = inventoryItems?.filter((item: any) => item.health_status === 'WARNING').length || 0
  const healthyCount = inventoryItems?.filter((item: any) => item.health_status === 'HEALTHY').length || 0
  const demandTrackedCount = inventoryItems?.filter((item: any) => !item.has_inventory_tracking).length || 0

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-3xl font-bold text-white">Inventory Intelligence</h2>
            <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-semibold px-2.5 py-0.5 rounded-full">
              {hasInventoryTracking ? 'Stockout Early Warning' : 'Demand Velocity Tracking'}
            </span>
          </div>
          <p className="text-slate-400">
            Automated supply-demand matching, sales velocity tracking, and stock depletion risk forecasting.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="bg-slate-800 text-slate-300 px-4 py-2 rounded-lg text-sm hover:bg-slate-700 hover:text-white transition flex items-center gap-2 self-start"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Re-scan Inventory
        </button>
      </header>

      {/* Non-fabrication Disclosure Banner */}
      {inventoryItems && inventoryItems.length > 0 && !hasInventoryTracking && (
        <div className="p-4 bg-blue-950/40 border border-blue-500/40 rounded-xl text-xs text-blue-200 flex items-start gap-3">
          <div className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">i</div>
          <div>
            <p className="font-semibold text-blue-300">Empirical Sales Velocity Mode (No Inventory Column in Ingested Data)</p>
            <p className="text-slate-300 mt-0.5">
              The currently imported dataset records sales transactions without an on-hand inventory (<code className="text-blue-300">available_stock</code>) field. The platform calculates true 30-day daily velocity and 7-day demand projections without fabricating synthetic warehouse stock counts.
            </p>
          </div>
        </div>
      )}

      {/* KPI Alert Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-surface p-5 rounded-xl border border-slate-700 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block mb-1">
              {hasInventoryTracking ? 'Critical Stockout Risks' : 'Monitored Products'}
            </span>
            <span className={`text-3xl font-bold ${hasInventoryTracking ? 'text-danger' : 'text-white'}`}>
              {hasInventoryTracking ? `${criticalCount} SKUs` : `${inventoryItems?.length || 0} SKUs`}
            </span>
            <span className="text-[11px] text-slate-400 block mt-1">
              {hasInventoryTracking ? 'Depletion < 5 days' : 'Active SKU demand tracks'}
            </span>
          </div>
          <div className="w-12 h-12 bg-danger/10 text-danger rounded-xl flex items-center justify-center text-xl font-bold">
            {hasInventoryTracking ? '!' : '📦'}
          </div>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-slate-700 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block mb-1">
              {hasInventoryTracking ? 'Reorder Attention' : 'Inventory Tracking'}
            </span>
            <span className={`text-3xl font-bold ${hasInventoryTracking ? 'text-amber-400' : 'text-slate-300'}`}>
              {hasInventoryTracking ? `${warningCount} SKUs` : 'Velocity Only'}
            </span>
            <span className="text-[11px] text-slate-400 block mt-1">
              {hasInventoryTracking ? 'Buffer 5–14 days' : 'Zero fabricated stock'}
            </span>
          </div>
          <div className="w-12 h-12 bg-amber-400/10 text-amber-400 rounded-xl flex items-center justify-center text-xl font-bold">
            {hasInventoryTracking ? '⚠' : '🔍'}
          </div>
        </div>

        <div className="bg-surface p-5 rounded-xl border border-slate-700 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block mb-1">
              {hasInventoryTracking ? 'Optimal Stocked' : 'Demand Forecasting'}
            </span>
            <span className={`text-3xl font-bold ${hasInventoryTracking ? 'text-emerald-400' : 'text-emerald-400'}`}>
              {hasInventoryTracking ? `${healthyCount} SKUs` : '7-Day Runways'}
            </span>
            <span className="text-[11px] text-slate-400 block mt-1">
              {hasInventoryTracking ? 'Sufficient runway' : 'Walk-forward evaluated'}
            </span>
          </div>
          <div className="w-12 h-12 bg-emerald-400/10 text-emerald-400 rounded-xl flex items-center justify-center text-xl font-bold">
            ✓
          </div>
        </div>
      </div>

      {/* Main Inventory Table */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 space-y-4 shadow-md">
        <div className="flex justify-between items-center border-b border-slate-700/60 pb-3">
          <h3 className="text-lg font-semibold text-white">SKU Inventory Depletion Register</h3>
          <span className="text-xs text-slate-400 font-mono">
            {inventoryItems ? `${inventoryItems.length} SKUs Monitored` : 'Loading...'}
          </span>
        </div>

        {isLoading && (
          <div className="py-12 text-center text-slate-400 animate-pulse">
            Analyzing SKU stock vs forecast demand runway...
          </div>
        )}

        {error && (
          <div className="p-4 bg-danger/20 border border-danger/50 text-danger rounded-lg text-sm">
            Failed to retrieve inventory metrics from backend API.
          </div>
        )}

        {!isLoading && (!inventoryItems || inventoryItems.length === 0) && (
          <div className="py-12 text-center text-slate-400 flex flex-col items-center justify-center space-y-3">
            <p className="text-slate-300 font-medium">No inventory or SKU data found.</p>
            <p className="text-xs text-slate-500 max-w-sm">
              Please import a dataset in Data Ingestion to analyze SKU stock runway and stockout alerts.
            </p>
            <a href="/data" className="text-xs text-primary hover:underline font-semibold">
              Go to Data Ingestion &rarr;
            </a>
          </div>
        )}

        {!isLoading && inventoryItems && inventoryItems.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-700 text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">SKU / Product</th>
                  <th className="py-3 px-4">Available Stock</th>
                  <th className="py-3 px-4">Daily Velocity</th>
                  <th className="py-3 px-4">7-Day Demand</th>
                  <th className="py-3 px-4">Runway (Days)</th>
                  <th className="py-3 px-4">Reorder Units</th>
                  <th className="py-3 px-4">Health Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-sm">
                {inventoryItems.map((item: any, idx: number) => {
                    const isCritical = item.health_status === 'CRITICAL'
                    const isWarning = item.health_status === 'WARNING'
                    const isOverstock = item.health_status === 'OVERSTOCK'
                    const isDemandOnly = !item.has_inventory_tracking || item.health_status === 'DEMAND_ONLY'

                    return (
                      <tr key={idx} className="hover:bg-slate-800/40 transition">
                        <td className="py-3.5 px-4 font-mono font-medium text-white">{item.sku}</td>
                        <td className="py-3.5 px-4 text-slate-200 font-medium">
                          {item.available_stock != null ? item.available_stock.toLocaleString() : (
                            <span className="text-xs text-slate-500 font-mono">N/A (Omitted)</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-slate-400">{item.daily_velocity} /day</td>
                        <td className="py-3.5 px-4 text-blue-300 font-medium">{item.forecast_7d_demand}</td>
                        <td className="py-3.5 px-4 font-semibold">
                          {item.days_of_supply != null ? (
                            <span className={isCritical ? 'text-danger' : isWarning ? 'text-amber-400' : 'text-slate-200'}>
                              {item.days_of_supply} days
                            </span>
                          ) : (
                            <span className="text-xs text-slate-500 font-normal">--</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          {item.reorder_suggested != null && item.reorder_suggested > 0 ? (
                            <span className="text-xs bg-primary/20 text-primary border border-primary/40 px-2 py-0.5 rounded font-mono font-semibold">
                              +{item.reorder_suggested}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-500">&mdash;</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          {isDemandOnly ? (
                            <span className="text-xs px-2.5 py-1 rounded-full font-semibold border bg-blue-500/10 text-blue-400 border-blue-500/40">
                              Demand Tracked
                            </span>
                          ) : (
                            <span
                              className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                                isCritical
                                  ? 'bg-danger/10 text-danger border-danger/40'
                                  : isWarning
                                  ? 'bg-amber-400/10 text-amber-400 border-amber-400/40'
                                  : isOverstock
                                  ? 'bg-purple-500/10 text-purple-400 border-purple-500/40'
                                  : 'bg-emerald-400/10 text-emerald-400 border-emerald-400/40'
                              }`}
                            >
                              {item.health_status}
                            </span>
                          )}
                        </td>
                      </tr>
                    )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

