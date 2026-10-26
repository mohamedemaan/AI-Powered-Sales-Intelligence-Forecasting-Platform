'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'
import { AlertTriangle, ShieldCheck, Search } from 'lucide-react'

interface SkuOption {
  sku: string
  label: string
  count: number
}

export default function AnomaliesPage() {
  const [sku, setSku] = useState('ALL')
  const [customSkuMode, setCustomSkuMode] = useState(false)

  // Fetch available SKUs
  const { data: skuOptions, isLoading: loadingSkus } = useQuery<SkuOption[]>({
    queryKey: ['available-skus'],
    queryFn: async () => {
      const res = await api.get('/api/v1/data/skus')
      return res.data
    }
  })

  const { data: anomalies, isLoading, error, refetch } = useQuery({
    queryKey: ['anomalies', sku],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/anomalies', {
        params: { sku }
      })
      return res.data
    }
  })

  return (
    <div className="space-y-6">
      <header>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-warning/20 text-warning">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-white">Anomaly Detection Center</h2>
            <p className="text-slate-400">Statistical outlier detection and volatility analysis using rolling Z-Score thresholds.</p>
          </div>
        </div>
      </header>

      {/* Filter Bar */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs text-slate-400">Target Product / SKU</label>
              <button 
                type="button"
                onClick={() => setCustomSkuMode(!customSkuMode)}
                className="text-xs text-primary hover:underline ml-3"
              >
                {customSkuMode ? 'Select from list' : 'Custom SKU'}
              </button>
            </div>

            {customSkuMode ? (
              <input 
                type="text" 
                value={sku} 
                onChange={(e) => setSku(e.target.value)}
                className="bg-background text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm min-w-[280px]"
                placeholder="Type SKU or 'ALL'"
              />
            ) : (
              <select
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                disabled={loadingSkus}
                className="bg-background text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm min-w-[300px]"
              >
                {skuOptions && skuOptions.length > 0 ? (
                  skuOptions.map((opt) => (
                    <option key={opt.sku} value={opt.sku}>
                      {opt.label}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="ALL">All SKUs (Global Aggregate)</option>
                    <option value="SKU-1001">SKU-1001 (Sample)</option>
                  </>
                )}
              </select>
            )}
          </div>
          <button 
            onClick={() => refetch()}
            className="mt-5 bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-600 transition flex items-center gap-2"
          >
            <Search className="h-4 w-4" />
            <span>Scan for Anomalies</span>
          </button>
        </div>

        <div className="text-right">
          <span className="text-xs text-slate-400 block">Detection Method</span>
          <span className="text-sm font-semibold text-slate-200">Z-Score Outlier (|Z| &ge; 2.0)</span>
        </div>
      </div>

      {/* Anomalies Table / List */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 space-y-4">
        <h3 className="text-lg font-semibold text-white">Detected Anomalies ({anomalies?.length || 0})</h3>

        {isLoading && <div className="text-slate-400 py-8 text-center">Scanning sales patterns...</div>}
        {error && <div className="text-danger py-4">Failed to load anomalies from backend.</div>}

        {!isLoading && (!anomalies || anomalies.length === 0) && (
          <div className="text-center py-12 text-slate-400 flex flex-col items-center">
            <ShieldCheck className="h-12 w-12 text-accent mb-2" />
            <p className="text-lg font-medium text-white mb-1">No Anomalies Detected</p>
            <p className="text-sm max-w-md">
              Sales patterns for <span className="text-white font-mono">{sku}</span> are within normal statistical tolerance boundaries.
            </p>
          </div>
        )}

        {!isLoading && anomalies && anomalies.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-800/80 text-slate-300 uppercase text-[11px] border-b border-slate-700">
                <tr>
                  <th className="px-3.5 py-3">Date</th>
                  <th className="px-3.5 py-3">Alert Type</th>
                  <th className="px-3.5 py-3 text-right">Observed Units</th>
                  <th className="px-3.5 py-3 text-right">Baseline Expected</th>
                  <th className="px-3.5 py-3 text-right">Z-Score</th>
                  <th className="px-3.5 py-3">Severity</th>
                  <th className="px-3.5 py-3">Investigation Guidance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {anomalies.map((item: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="px-3.5 py-3 text-white font-mono whitespace-nowrap">{item.date}</td>
                    <td className="px-3.5 py-3 font-medium text-slate-200 whitespace-nowrap">
                      {item.alert_type || 'Outlier Event'}
                    </td>
                    <td className="px-3.5 py-3 text-right text-white font-semibold">{item.units_sold}</td>
                    <td className="px-3.5 py-3 text-right text-slate-400 font-mono">
                      {item.expected_units !== undefined ? item.expected_units : '--'}
                    </td>
                    <td className="px-3.5 py-3 text-right font-mono text-slate-300">
                      {item.z_score !== undefined ? `${item.z_score >= 0 ? '+' : ''}${item.z_score.toFixed(2)}` : '--'}
                    </td>
                    <td className="px-3.5 py-3 whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        item.anomaly_severity === 'High' ? 'bg-danger/20 text-danger border border-danger/30' :
                        item.anomaly_severity === 'Medium' ? 'bg-warning/20 text-warning border border-warning/30' :
                        'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}>
                        {item.anomaly_severity}
                      </span>
                    </td>
                    <td className="px-3.5 py-3 text-slate-300 max-w-xs text-[11px]">
                      {item.guidance || 'Verify historical transaction logs against seasonal promotions or channel delivery.'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
