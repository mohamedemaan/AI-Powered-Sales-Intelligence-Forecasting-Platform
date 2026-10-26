'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'

interface SkuOption {
  sku: string
  label: string
  count: number
}

export default function ScenariosPage() {
  const [sku, setSku] = useState('ALL')
  const [customSkuMode, setCustomSkuMode] = useState(false)
  const [priceChange, setPriceChange] = useState<number>(0)
  const [discount, setDiscount] = useState<number>(10)
  const [demandMult, setDemandMult] = useState<number>(1.0)
  const [isSimulating, setIsSimulating] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Fetch available SKUs
  const { data: skuOptions, isLoading: loadingSkus } = useQuery<SkuOption[]>({
    queryKey: ['available-skus'],
    queryFn: async () => {
      const res = await api.get('/api/v1/data/skus')
      return res.data
    }
  })

  const handleSimulate = async () => {
    setIsSimulating(true)
    setErrorMsg(null)

    try {
      const res = await api.post('/api/v1/analytics/simulate', null, {
        params: {
          sku: sku || 'ALL',
          price_change: priceChange,
          discount: discount,
          demand_mult: demandMult
        }
      })
      if (res.data.error) {
        setErrorMsg(res.data.error)
      } else {
        setResult(res.data)
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Simulation failed. Check that backend is running.')
    } finally {
      setIsSimulating(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header>
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-3xl font-bold text-white">Scenario Simulation Lab</h2>
          <span className="text-xs bg-primary/20 text-primary border border-primary/40 font-semibold px-2.5 py-0.5 rounded-full">
            What-If Modeling
          </span>
        </div>
        <p className="text-slate-400">
          Simulate commercial changes in pricing, discount promotions, and demand assumptions with integrated price elasticity.
        </p>
      </header>

      {/* Control Configuration Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-surface p-6 rounded-xl border border-slate-700 space-y-5 md:col-span-1 shadow-md">
          <h3 className="text-lg font-semibold text-white border-b border-slate-700/60 pb-3">
            Simulation Parameters
          </h3>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs text-slate-400 font-medium">Target SKU</label>
              <button 
                type="button"
                onClick={() => setCustomSkuMode(!customSkuMode)}
                className="text-xs text-primary hover:underline"
              >
                {customSkuMode ? 'Select from list' : 'Custom SKU'}
              </button>
            </div>

            {customSkuMode ? (
              <input
                type="text"
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                className="w-full bg-background text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono"
                placeholder="Type SKU or 'ALL'"
              />
            ) : (
              <select
                value={sku}
                onChange={(e) => setSku(e.target.value)}
                disabled={loadingSkus}
                className="w-full bg-background text-white px-3 py-2 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm font-mono"
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
                  </>
                )}
              </select>
            )}
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Price Adjustment (%)</span>
              <span className={`font-mono font-semibold ${priceChange >= 0 ? 'text-emerald-400' : 'text-danger'}`}>
                {priceChange >= 0 ? `+${priceChange}%` : `${priceChange}%`}
              </span>
            </div>
            <input
              type="range"
              min="-50"
              max="50"
              step="5"
              value={priceChange}
              onChange={(e) => setPriceChange(Number(e.target.value))}
              className="w-full accent-primary cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>-50%</span>
              <span>Baseline (0%)</span>
              <span>+50%</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Promotional Discount (%)</span>
              <span className="text-accent font-mono font-semibold">{discount}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="60"
              step="5"
              value={discount}
              onChange={(e) => setDiscount(Number(e.target.value))}
              className="w-full accent-accent cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0% (Full Price)</span>
              <span>30%</span>
              <span>60% (Flash Sale)</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-400">Macro Demand Multiplier</span>
              <span className="text-blue-400 font-mono font-semibold">{demandMult.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={demandMult}
              onChange={(e) => setDemandMult(Number(e.target.value))}
              className="w-full accent-blue-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0.5x (Recession)</span>
              <span>1.0x (Normal)</span>
              <span>2.0x (Viral/Peak)</span>
            </div>
          </div>

          <button
            onClick={handleSimulate}
            disabled={isSimulating}
            className="w-full bg-primary text-white py-2.5 rounded-lg font-medium hover:bg-blue-600 transition shadow-md disabled:opacity-50"
          >
            {isSimulating ? 'Simulating Elasticity...' : 'Run Scenario Simulation'}
          </button>
        </div>

        {/* Results Panel */}
        <div className="bg-surface p-6 rounded-xl border border-slate-700 md:col-span-2 space-y-6 shadow-md flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white border-b border-slate-700/60 pb-3 mb-4">
              Projected Commercial Impact
            </h3>

            {errorMsg && (
              <div className="p-4 bg-danger/10 border border-danger/40 text-danger rounded-xl text-sm mb-4">
                {errorMsg}
              </div>
            )}

            {!result && !errorMsg && (
              <div className="h-64 flex flex-col items-center justify-center text-slate-500 space-y-2">
                <svg className="w-12 h-12 text-slate-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p>Configure parameters on the left and click "Run Scenario Simulation".</p>
              </div>
            )}

            {result && (
              <div className="space-y-6">
                {/* Metric Summary Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-background/80 p-4 rounded-xl border border-slate-700">
                    <span className="text-xs text-slate-400 block mb-1">Projected 7-Day Revenue</span>
                    <span className="text-2xl font-bold text-white">${result.projected_revenue?.toLocaleString()}</span>
                    <div className="mt-1 flex items-center gap-1">
                      <span className={`text-xs font-semibold ${result.revenue_delta_pct >= 0 ? 'text-emerald-400' : 'text-danger'}`}>
                        {result.revenue_delta_pct >= 0 ? `+${result.revenue_delta_pct}%` : `${result.revenue_delta_pct}%`}
                      </span>
                      <span className="text-[10px] text-slate-500">vs. baseline (${result.baseline_revenue?.toLocaleString()})</span>
                    </div>
                  </div>

                  <div className="bg-background/80 p-4 rounded-xl border border-slate-700">
                    <span className="text-xs text-slate-400 block mb-1">Units Projected</span>
                    <span className="text-2xl font-bold text-white">{result.units_projected}</span>
                    <div className="mt-1 flex items-center gap-1">
                      <span className="text-xs font-semibold text-blue-400">
                        {result.units_projected >= result.units_baseline ? `+${(result.units_projected - result.units_baseline).toFixed(1)} units` : `${(result.units_projected - result.units_baseline).toFixed(1)} units`}
                      </span>
                      <span className="text-[10px] text-slate-500">vs. baseline ({result.units_baseline})</span>
                    </div>
                  </div>

                  <div className="bg-background/80 p-4 rounded-xl border border-slate-700">
                    <span className="text-xs text-slate-400 block mb-1">Stockout Risk Level</span>
                    <span className={`text-sm font-bold block ${result.stockout_risk?.includes('High') ? 'text-danger' : result.stockout_risk?.includes('Moderate') ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {result.stockout_risk}
                    </span>
                    <span className="text-[10px] text-slate-400 mt-1 block">Effective Unit Price: ${result.price_effective}</span>
                  </div>
                </div>

                {/* Day by Day Table */}
                <div className="border border-slate-700 rounded-xl overflow-hidden">
                  <div className="bg-slate-800/80 px-4 py-2.5 text-xs font-semibold text-slate-300">
                    7-Day Trajectory Comparison (Units)
                  </div>
                  <div className="divide-y divide-slate-700/60 bg-background/50">
                    {result.simulated_predictions?.map((simVal: number, idx: number) => {
                      const baseVal = result.baseline_predictions?.[idx] || 0
                      const diff = (simVal - baseVal).toFixed(1)
                      return (
                        <div key={idx} className="flex justify-between items-center px-4 py-2.5 text-xs">
                          <span className="text-slate-400 font-medium">Day +{idx + 1}</span>
                          <span className="text-slate-500">Baseline: {baseVal} units</span>
                          <span className="text-white font-semibold">Simulated: {simVal} units</span>
                          <span className={`font-mono font-semibold ${Number(diff) >= 0 ? 'text-emerald-400' : 'text-danger'}`}>
                            {Number(diff) >= 0 ? `+${diff}` : diff}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="text-[11px] text-slate-500 pt-3 border-t border-slate-800">
            * Models demand response using price elasticity coefficient ($E_d = -0.75$) and promotional discount lift ($E_p = 1.4$).
          </div>
        </div>
      </div>
    </div>
  )
}
