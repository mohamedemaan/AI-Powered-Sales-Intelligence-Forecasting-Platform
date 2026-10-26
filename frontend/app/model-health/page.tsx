'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import api from '../../lib/api'
import {
  Activity,
  History,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  CheckCircle2,
  Calendar,
  Layers,
  Clock
} from 'lucide-react'

export default function ModelHealthPage() {
  const [activeTab, setActiveTab] = useState<'telemetry' | 'history'>('telemetry')
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evalFeedback, setEvalFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  const { data: health, isLoading: loadingHealth, refetch: refetchHealth } = useQuery({
    queryKey: ['model-health-dashboard'],
    queryFn: async () => {
      const res = await api.get('/api/v1/analytics/model-health')
      return res.data
    }
  })

  const { data: historyData, isLoading: loadingHistory, refetch: refetchHistory } = useQuery({
    queryKey: ['prediction-history-audit'],
    queryFn: async () => {
      const res = await api.get('/api/v1/ml/history')
      return res.data
    }
  })

  const runs = historyData?.runs || []

  const handleRunEvaluation = async () => {
    setIsEvaluating(true)
    setEvalFeedback(null)
    try {
      await api.post('/api/v1/ml/train?sku=ALL&forecast_days=7')
      await Promise.all([refetchHealth(), refetchHistory()])
      setEvalFeedback({
        message: 'Walk-forward model evaluation completed and logged to database successfully.',
        type: 'success'
      })
    } catch (err: any) {
      try {
        await api.post('/api/v1/ml/analyze', { target_name: 'ALL', mode: 'range' })
        await Promise.all([refetchHealth(), refetchHistory()])
        setEvalFeedback({
          message: 'Model analyzed and metrics persisted to database successfully.',
          type: 'success'
        })
      } catch (err2: any) {
        setEvalFeedback({
          message: err?.response?.data?.detail || err2?.response?.data?.detail || 'Evaluation failed. Please ensure a valid dataset is uploaded.',
          type: 'error'
        })
      }
    } finally {
      setIsEvaluating(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-3xl font-bold tracking-tight text-white">Model Health & Prediction History</h2>
            <span className="text-xs bg-blue-500/20 text-blue-400 border border-blue-500/40 font-semibold px-2.5 py-0.5 rounded-full">
              Production Telemetry
            </span>
          </div>
          <p className="text-slate-400 text-sm">
            Continuous walk-forward cross-validation evaluation, WAPE error tracking, and prediction history audit logs.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start">
          <button
            onClick={handleRunEvaluation}
            disabled={isEvaluating}
            className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-background font-semibold px-4 py-2 rounded-lg text-xs transition disabled:opacity-50"
          >
            {isEvaluating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Evaluating Models...
              </>
            ) : (
              <>
                <TrendingUp className="w-3.5 h-3.5" /> Run Walk-Forward Benchmark
              </>
            )}
          </button>

          <button
            onClick={() => { refetchHealth(); refetchHistory(); }}
            className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3 py-2 rounded-lg text-xs font-medium transition"
            title="Refresh Telemetry"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {evalFeedback && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center justify-between border ${
            evalFeedback.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}
        >
          <span>{evalFeedback.message}</span>
          <button
            onClick={() => setEvalFeedback(null)}
            className="text-slate-400 hover:text-white text-sm leading-none ml-4"
          >
            &times;
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-1">
        <button
          onClick={() => setActiveTab('telemetry')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
            activeTab === 'telemetry'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <Activity className="w-4 h-4" />
          Evaluation Telemetry & Drift
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
            activeTab === 'history'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-400 hover:text-white hover:border-slate-700'
          }`}
        >
          <History className="w-4 h-4" />
          Prediction History & Actuals Audit ({runs.length})
        </button>
      </div>

      {/* TAB 1: TELEMETRY & DRIFT */}
      {activeTab === 'telemetry' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="bg-surface p-5 rounded-xl border border-slate-700">
              <span className="text-xs text-slate-400 block mb-1">Active Model</span>
              <span className="text-lg font-bold text-white block truncate" title={health?.active_model || health?.model_name || 'No Active Model'}>
                {loadingHealth ? 'Loading...' : health?.active_model || health?.model_name || 'No Active Model'}
              </span>
              <span className={`text-[11px] font-semibold mt-1 block ${health?.model_status === 'HEALTHY' ? 'text-emerald-400' : 'text-slate-400'}`}>
                Status: {health?.model_status || 'UNINITIALIZED'}
              </span>
            </div>

            <div className="bg-surface p-5 rounded-xl border border-slate-700">
              <span className="text-xs text-slate-400 block mb-1">WAPE (Weighted Error)</span>
              <span className="text-2xl font-bold text-white">
                {loadingHealth ? '...' : health?.avg_wape != null ? `${health.avg_wape}%` : health?.wape != null ? `${health.wape}%` : '--'}
              </span>
              <span className="text-[11px] text-emerald-400 font-semibold mt-1 block">
                Target: &le; 12.0%
              </span>
            </div>

            <div className="bg-surface p-5 rounded-xl border border-slate-700">
              <span className="text-xs text-slate-400 block mb-1">Mean Absolute Error (MAE)</span>
              <span className="text-2xl font-bold text-white">
                {loadingHealth ? '...' : health?.avg_mae != null ? `${health.avg_mae} units` : health?.mae != null ? `${health.mae} units` : '--'}
              </span>
              <span className="text-[11px] text-slate-400 mt-1 block">
                RMSE: {health?.avg_rmse != null ? health.avg_rmse : health?.rmse != null ? health.rmse : '--'}
              </span>
            </div>

            <div className="bg-surface p-5 rounded-xl border border-slate-700">
              <span className="text-xs text-slate-400 block mb-1">Model Drift Signal</span>
              <span className="text-2xl font-bold text-emerald-400">
                {loadingHealth ? '...' : health?.drift_status || 'No Recorded Runs'}
              </span>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Drift Score: {health?.drift_score != null ? health.drift_score : 'N/A'}
              </span>
            </div>
          </div>

          {/* Validation Strategy Overview */}
          <div className="bg-surface p-6 rounded-xl border border-slate-700 space-y-4 shadow-sm">
            <h3 className="text-base font-semibold text-white border-b border-slate-700/60 pb-3">
              Validation Protocol & Benchmarking Architecture
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="bg-background/80 p-4 rounded-lg border border-slate-700/80">
                <span className="font-semibold text-primary uppercase block mb-1">Cross-Validation</span>
                <p className="text-slate-300">
                  {health?.validation_strategy || 'Walk-Forward Rolling Cross-Validation'} ensures zero lookahead bias or future-data leakage into model weights.
                </p>
              </div>

              <div className="bg-background/80 p-4 rounded-lg border border-slate-700/80">
                <span className="font-semibold text-blue-400 uppercase block mb-1">Baseline Comparison</span>
                <p className="text-slate-300">
                  Candidate ARIMA forecasts are continually evaluated against 7-day Seasonal Naive baseline to ensure complexity delivers superior accuracy.
                </p>
              </div>

              <div className="bg-background/80 p-4 rounded-lg border border-slate-700/80">
                <span className="font-semibold text-emerald-400 uppercase block mb-1">Drift Threshold</span>
                <p className="text-slate-300">
                  When WAPE exceeds 15% across two consecutive windows, automated alerts flag candidate retrain triggers.
                </p>
              </div>
            </div>

            {/* History Table */}
            <div className="pt-4">
              <h4 className="text-sm font-semibold text-slate-300 mb-3">Recent Model Evaluation Runs</h4>
              {loadingHealth && <p className="text-xs text-slate-500 py-4">Fetching historical model telemetry...</p>}

              {!loadingHealth && health?.last_trained_runs && health.last_trained_runs.length > 0 ? (
                <div className="border border-slate-700 rounded-lg overflow-hidden">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-800/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-700">
                        <th className="py-2.5 px-3">Run ID</th>
                        <th className="py-2.5 px-3">Scope / SKU</th>
                        <th className="py-2.5 px-3">Model Version</th>
                        <th className="py-2.5 px-3">MAE</th>
                        <th className="py-2.5 px-3">RMSE</th>
                        <th className="py-2.5 px-3">WAPE</th>
                        <th className="py-2.5 px-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 bg-background/40">
                      {health.last_trained_runs.map((run: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-mono text-slate-400">{run.id.slice(0, 8)}...</td>
                          <td className="py-2.5 px-3 font-medium text-white">{run.sku}</td>
                          <td className="py-2.5 px-3 text-slate-300 font-mono">{run.model_version}</td>
                          <td className="py-2.5 px-3 text-slate-200">{run.mae != null ? run.mae : '--'}</td>
                          <td className="py-2.5 px-3 text-slate-200">{run.rmse != null ? run.rmse : '--'}</td>
                          <td className="py-2.5 px-3 font-semibold text-emerald-400">
                            {run.wape != null ? `${run.wape}%` : '--'}
                          </td>
                          <td className="py-2.5 px-3">
                            <span className="text-[10px] bg-emerald-400/20 text-emerald-400 px-2 py-0.5 rounded font-mono font-semibold">
                              {run.status || 'SUCCESS'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-6 bg-background/50 rounded-lg border border-slate-800 text-xs text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div>
                    <span className="font-semibold text-white block mb-1">No Historical Model Runs Recorded</span>
                    <p className="text-slate-400">
                      Upload sales records or run walk-forward evaluation to benchmark baseline and ARIMA models.
                    </p>
                  </div>
                  <button
                    onClick={handleRunEvaluation}
                    disabled={isEvaluating}
                    className="inline-flex items-center gap-2 bg-primary/20 text-primary border border-primary/40 hover:bg-primary/30 px-4 py-2 rounded-lg font-semibold transition disabled:opacity-50 whitespace-nowrap"
                  >
                    {isEvaluating ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Evaluating...
                      </>
                    ) : (
                      <>
                        <TrendingUp className="w-3.5 h-3.5" /> Run Walk-Forward Benchmark Now
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PREDICTION HISTORY & ACTUALS AUDIT */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="bg-surface p-4 rounded-xl border border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-white">Saved Prediction Logs & Ground Truth Comparisons</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Every forecast generated via Forecast Lab is persisted with its training horizon, parameters, and ground truth reconciliation.
              </p>
            </div>
            <Link
              href="/forecast"
              className="inline-flex items-center gap-1.5 text-xs text-primary font-semibold border border-primary/30 bg-primary/10 px-3 py-1.5 rounded-lg hover:bg-primary/20 transition"
            >
              Run New Forecast in Lab &rarr;
            </Link>
          </div>

          {loadingHistory ? (
            <div className="h-64 flex items-center justify-center text-slate-500">
              <p className="animate-pulse">Loading prediction audit history...</p>
            </div>
          ) : runs.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Runs List */}
              <div className="lg:col-span-1 space-y-2">
                <span className="text-xs text-slate-400 font-medium block mb-1">Historical Model Runs</span>
                {runs.map((r: any) => {
                  const isSelected = selectedRun?.run_id === r.run_id
                  return (
                    <div
                      key={r.run_id}
                      onClick={() => setSelectedRun(r)}
                      className={`p-3.5 rounded-xl border transition cursor-pointer ${
                        isSelected
                          ? 'bg-primary/15 border-primary text-white shadow-sm'
                          : 'bg-surface border-slate-700/80 hover:border-slate-600 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs text-white truncate max-w-[150px]">
                          {r.sku}
                        </span>
                        <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-primary">
                          {r.model_version}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2">
                        <span>Horizon: {r.predictions_count} days</span>
                        {r.metrics?.wape && <span>WAPE: {r.metrics.wape}%</span>}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1 font-mono">
                        {r.created_at?.slice(0, 19).replace('T', ' ')}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Run Predictions Details & Actuals Comparison */}
              <div className="lg:col-span-2">
                {selectedRun ? (
                  <div className="bg-surface rounded-xl border border-slate-700 p-5 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div>
                        <h4 className="text-sm font-semibold text-white">
                          Run Details: {selectedRun.sku} ({selectedRun.model_version})
                        </h4>
                        <span className="text-[11px] text-slate-400 font-mono">Run ID: {selectedRun.run_id}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        {selectedRun.metrics?.mae && (
                          <span className="bg-slate-800 px-2.5 py-1 rounded text-slate-300">
                            MAE: {selectedRun.metrics.mae}
                          </span>
                        )}
                        {selectedRun.metrics?.rmse && (
                          <span className="bg-slate-800 px-2.5 py-1 rounded text-slate-300">
                            RMSE: {selectedRun.metrics.rmse}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-800/80 text-slate-300 border-b border-slate-700">
                          <tr>
                            <th className="py-2 px-3">Forecast Date</th>
                            <th className="py-2 px-3 text-right">Predicted (Units)</th>
                            <th className="py-2 px-3 text-right">Actual (Units)</th>
                            <th className="py-2 px-3 text-right">Variance</th>
                            <th className="py-2 px-3 text-right">Ground Truth Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {selectedRun.predictions?.map((p: any, idx: number) => (
                            <tr key={idx} className="hover:bg-slate-800/40">
                              <td className="py-2 px-3 font-mono text-slate-300">{p.forecast_date}</td>
                              <td className="py-2 px-3 text-right font-medium text-white">{p.predicted_demand}</td>
                              <td className="py-2 px-3 text-right text-slate-200">
                                {p.actual_demand !== null ? p.actual_demand : '--'}
                              </td>
                              <td className="py-2 px-3 text-right">
                                {p.variance !== null ? (
                                  <span className={Math.abs(p.variance) <= 5 ? 'text-emerald-400' : 'text-amber-400'}>
                                    {p.variance >= 0 ? `+${p.variance}` : p.variance}
                                  </span>
                                ) : (
                                  <span className="text-slate-500">Pending</span>
                                )}
                              </td>
                              <td className="py-2 px-3 text-right">
                                <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                                  p.status === 'Verified Actual'
                                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                                }`}>
                                  {p.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="h-64 border border-dashed border-slate-800 rounded-xl flex flex-col items-center justify-center p-6 text-center text-slate-500">
                    <p>Select a model run on the left to inspect prediction trajectory vs. actual sales.</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-surface p-8 rounded-xl border border-dashed border-slate-800 text-center text-slate-400 space-y-3">
              <p>No saved prediction runs found in the database.</p>
              <p className="text-xs text-slate-500">
                Run an analysis in the Forecast Lab or trigger model training to generate and persist verified prediction logs.
              </p>
              <Link
                href="/forecast"
                className="inline-flex items-center gap-1.5 bg-primary text-white text-xs px-4 py-2 rounded-lg hover:bg-blue-600 transition"
              >
                Go to Forecast Lab
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
