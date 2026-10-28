'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import api from '../../lib/api'

interface SkuOption {
  sku: string
  label: string
  count: number
}

export default function GeminiPage() {
  const [query, setQuery] = useState('')
  const [sku, setSku] = useState('ALL')
  const [response, setResponse] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Fetch available SKUs
  const { data: skuOptions } = useQuery<SkuOption[]>({
    queryKey: ['available-skus'],
    queryFn: async () => {
      const res = await api.get('/api/v1/data/skus')
      return res.data
    }
  })

  const askGemini = async () => {
    if (!query.trim()) return

    setIsLoading(true)
    setErrorMsg(null)
    setResponse(null)

    try {
      const res = await api.post(
        '/api/v1/analytics/gemini',
        { query, sku: sku || 'ALL' },
        {
          params: { query, sku: sku || 'ALL' },
          timeout: 60000
        }
      )
      setResponse(res.data)
    } catch (err: any) {
      const backendMsg = err.response?.data?.detail || err.response?.data?.answer || err.response?.data?.message
      if (backendMsg) {
        setErrorMsg(backendMsg)
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setErrorMsg('Request timed out. Google Gemini is taking longer than expected. Please try again.')
      } else if (err.message === 'Network Error') {
        setErrorMsg('Failed to reach FastAPI backend at http://127.0.0.1:8000. Ensure the backend server is running.')
      } else {
        setErrorMsg(err.message || 'Failed to reach Gemini Pro backend service.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const promptOptions = [
    'Why did sales drop last week?',
    'What is the forecasted demand trend for next month?',
    'Identify inventory risks and stockout anomalies',
    'Recommend top revenue optimization actions'
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <header className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-3xl font-bold text-white">Gemini Pro Sales Advisor</h2>
            <span className="text-xs bg-gradient-to-r from-blue-500 to-indigo-500 text-white font-semibold px-2.5 py-0.5 rounded-full shadow-sm">
              Powered by Google Gemini
            </span>
          </div>
          <p className="text-slate-400">Context-aware generative intelligence grounded in your live sales data, stock levels, and forecasting models.</p>
        </div>
      </header>
      
      <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-md space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-xs text-slate-400 font-medium">Business Scope / Target Product</label>
          <select
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            className="bg-background text-white text-xs px-3 py-1.5 rounded-lg border border-slate-600 focus:outline-none focus:border-primary min-w-[260px]"
          >
            {skuOptions && skuOptions.length > 0 ? (
              skuOptions.map((opt, idx) => (
                <option key={`${opt.sku}-${idx}`} value={opt.sku}>
                  {opt.label}
                </option>
              ))
            ) : (
              <option value="ALL">All SKUs (Global Store Data)</option>
            )}
          </select>
        </div>

        <textarea 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask Gemini Pro about sales anomalies, seasonal patterns, or forecast advice (e.g. 'How should we adjust safety stock for next month?')..."
          className="w-full bg-background text-white p-4 rounded-lg border border-slate-600 focus:outline-none focus:border-primary h-32 transition"
        />
        
        <div className="mt-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            {promptOptions.map((opt, idx) => (
              <button 
                key={idx}
                type="button" 
                onClick={() => setQuery(opt)}
                className="text-xs bg-slate-800 text-slate-300 px-3 py-1.5 rounded-md hover:bg-slate-700 hover:text-white border border-slate-700 transition"
              >
                {opt}
              </button>
            ))}
          </div>

          <button 
            onClick={askGemini} 
            disabled={isLoading || !query.trim()}
            className="w-full md:w-auto bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-2.5 rounded-lg font-medium hover:from-blue-500 hover:to-indigo-500 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                Consulting Gemini Pro...
              </span>
            ) : (
              'Ask Gemini Pro'
            )}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger/20 border border-danger/50 text-danger rounded-lg text-sm">
          {errorMsg}
        </div>
      )}

      {response && (
        <div className="bg-gradient-to-b from-blue-950/40 to-slate-900/60 border border-blue-500/40 p-6 rounded-xl space-y-5 shadow-lg">
          <div className="flex justify-between items-center border-b border-slate-700/60 pb-3">
            <h4 className="text-lg font-semibold text-blue-400 flex items-center gap-2">
              <span>✦</span> Gemini Intelligence Insights
            </h4>
            {response.model && (
              <span className="text-xs font-mono bg-blue-900/50 text-blue-300 border border-blue-700/50 px-2 py-0.5 rounded">
                Model: {response.model}
              </span>
            )}
          </div>
          
          <div className="prose prose-invert max-w-none text-white text-base leading-relaxed">
            <p className="whitespace-pre-line">{response.answer}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="bg-surface/90 p-4 rounded-lg border border-slate-700/80">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Empirical Evidence & Grounding Data
              </span>
              <pre className="text-blue-300 text-xs font-mono whitespace-pre-wrap bg-background/60 p-3 rounded border border-slate-700/50 overflow-x-auto">
                {typeof response.evidence === 'string' ? response.evidence : JSON.stringify(response.evidence, null, 2)}
              </pre>
            </div>
            
            <div className="bg-surface/90 p-4 rounded-lg border border-slate-700/80 flex flex-col justify-between">
              <div>
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block mb-2">
                  Actionable Business Recommendation
                </span>
                <p className="text-white text-sm leading-relaxed">
                  {response.recommendation}
                </p>
              </div>
              <div className="mt-3 text-[11px] text-slate-400">
                Ground truth based on current transaction history and ARIMA forecast bounds.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

