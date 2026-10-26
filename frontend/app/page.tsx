'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '../hooks/useAuth'
import {
  ArrowRight,
  TrendingUp,
  Activity,
  ShieldCheck,
  BarChart3,
  Sparkles,
  Zap,
  Layers,
  LineChart,
  Brain,
  Database,
  Lock
} from 'lucide-react'

export default function WelcomePage() {
  const router = useRouter()
  const { user } = useAuth()
  
  // Staged animation reveal sequence
  // 0: Initial state (mount)
  // 1: Background grid & ambient gradients (100ms)
  // 2: Connected data nodes & network lines (300ms)
  // 3: Sales trend charts & floating cards (600ms)
  // 4: Brand project name 'SalesMind AI' reveal (900ms)
  // 5: Main Heading 'Welcome to SalesMind AI' (1100ms)
  // 6: Supporting descriptive text (1300ms)
  // 7: Primary 'Get Started' button & interactive CTAs (1500ms)
  const [animStage, setAnimStage] = useState(0)
  const [isExiting, setIsExiting] = useState(false)

  useEffect(() => {
    const timers = [
      setTimeout(() => setAnimStage(1), 80),
      setTimeout(() => setAnimStage(2), 250),
      setTimeout(() => setAnimStage(3), 500),
      setTimeout(() => setAnimStage(4), 800),
      setTimeout(() => setAnimStage(5), 1050),
      setTimeout(() => setAnimStage(6), 1250),
      setTimeout(() => setAnimStage(7), 1450),
    ]
    return () => timers.forEach(clearTimeout)
  }, [])

  const handleGetStarted = (targetMode: 'register' | 'login' = 'register') => {
    setIsExiting(true)
    setTimeout(() => {
      router.push(`/login?mode=${targetMode}`)
    }, 280)
  }

  return (
    <div className={`min-h-screen bg-[#070d1e] text-slate-100 flex flex-col justify-between relative overflow-hidden transition-all duration-300 ${
      isExiting ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
    }`}>
      {/* =========================================================================
          BACKGROUND LAYER: Cyber grid, radiant teal/blue glows, connected network
          ========================================================================= */}
      <div 
        className={`absolute inset-0 bg-cyber-grid pointer-events-none transition-opacity duration-1000 ${
          animStage >= 1 ? 'opacity-80' : 'opacity-0'
        }`}
      />
      
      {/* Radiant Glow Orbs */}
      <div 
        className={`absolute -top-40 left-1/2 -translate-x-1/2 w-[750px] h-[450px] bg-gradient-to-b from-blue-600/20 via-cyan-500/15 to-transparent rounded-full blur-3xl pointer-events-none transition-all duration-1000 ${
          animStage >= 1 ? 'opacity-100 scale-100' : 'opacity-0 scale-75'
        }`}
      />
      <div 
        className={`absolute top-1/3 -left-32 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none transition-all duration-1000 delay-200 ${
          animStage >= 1 ? 'opacity-100' : 'opacity-0'
        }`}
      />
      <div 
        className={`absolute bottom-20 -right-20 w-96 h-96 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none transition-all duration-1000 delay-300 ${
          animStage >= 1 ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* =========================================================================
          TOP NAVIGATION BAR
          ========================================================================= */}
      <header className="relative z-20 max-w-7xl w-full mx-auto px-6 py-6 flex items-center justify-between">
        <div className={`flex items-center gap-3 transition-all duration-700 ${
          animStage >= 4 ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
        }`}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-cyan-500 to-teal-400 p-0.5 shadow-lg shadow-cyan-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-[#070d1e] rounded-[10px] flex items-center justify-center">
              <Brain className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-tight text-white flex items-center gap-1">
              SalesMind <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-teal-300">AI</span>
            </span>
            <span className="text-[10px] tracking-wider uppercase text-slate-400 font-mono block -mt-1">
              Enterprise Intelligence
            </span>
          </div>
        </div>

        {/* Right Nav Options */}
        <div className={`flex items-center gap-3 transition-all duration-700 delay-100 ${
          animStage >= 4 ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'
        }`}>
          {user ? (
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition shadow-sm"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Open Dashboard ({user.email.split('@')[0]})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          ) : (
            <>
              <button
                onClick={() => handleGetStarted('login')}
                className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white transition"
              >
                Sign In
              </button>
              <button
                onClick={() => handleGetStarted('register')}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-md shadow-blue-500/20 transition hover:scale-[1.02]"
              >
                <span>Get Started</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </header>

      {/* =========================================================================
          HERO SECTION: Sequence 4, 5, 6, 7
          ========================================================================= */}
      <main className="relative z-10 max-w-7xl w-full mx-auto px-6 py-6 md:py-10 flex-1 flex flex-col justify-center">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          {/* Left Column: Headlines & CTA */}
          <div className="lg:col-span-6 space-y-6 text-center lg:text-left">
            
            {/* Step 4: Project Tag & Badge */}
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-cyan-500/30 text-cyan-300 text-xs font-medium shadow-inner transition-all duration-700 ${
              animStage >= 4 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}>
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              <span className="font-semibold">AI-Powered Sales Intelligence & Forecasting Platform</span>
            </div>

            {/* Step 5: Main Heading */}
            <h1 className={`text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-white leading-[1.1] transition-all duration-700 ${
              animStage >= 5 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
            }`}>
              Welcome to <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-300 to-teal-300">
                SalesMind AI
              </span>
            </h1>

            {/* Step 6: Supporting Text */}
            <p className={`text-base sm:text-lg text-slate-300 max-w-xl mx-auto lg:mx-0 leading-relaxed font-normal transition-all duration-700 ${
              animStage >= 6 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
            }`}>
              Turn your sales data into intelligent predictions, actionable insights, and smarter business decisions.
            </p>

            {/* Step 7: Action Buttons & Security Assurance */}
            <div className={`pt-2 space-y-4 transition-all duration-700 ${
              animStage >= 7 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
            }`}>
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
                <button
                  onClick={() => handleGetStarted('register')}
                  className="w-full sm:w-auto px-8 py-4 rounded-xl font-bold text-base bg-gradient-to-r from-blue-600 via-cyan-600 to-teal-500 hover:from-blue-500 hover:via-cyan-500 hover:to-teal-400 text-white shadow-xl shadow-cyan-500/25 transition-all duration-200 hover:scale-[1.03] active:scale-[0.98] flex items-center justify-center gap-2 group cursor-pointer"
                >
                  <span>Get Started</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>

                <button
                  onClick={() => handleGetStarted('login')}
                  className="w-full sm:w-auto px-6 py-4 rounded-xl font-semibold text-sm bg-slate-900/90 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 transition-all duration-200 flex items-center justify-center gap-2"
                >
                  <Lock className="w-4 h-4 text-slate-400" />
                  <span>Sign In to Account</span>
                </button>
              </div>

              {/* Verified Trust Badges */}
              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-6 pt-2 text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  Bcrypt & JWT Auth
                </span>
                <span className="flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Auto-ARIMA Telemetry
                </span>
                <span className="flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-blue-400" />
                  RFC 4180 Ledger Audit
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Steps 2 & 3 Interactive Animated Data Visualization */}
          <div className="lg:col-span-6 relative">
            <div className={`relative transition-all duration-1000 ${
              animStage >= 3 ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-90 translate-y-8'
            }`}>
              
              {/* Glassmorphic Chart Centerpiece */}
              <div className="bg-[#0f172a]/90 backdrop-blur-xl border border-slate-700/70 rounded-2xl p-6 shadow-2xl shadow-cyan-950/40 relative overflow-hidden">
                
                {/* Header bar of visualization */}
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <div className="w-3 h-3 rounded-full bg-danger/80"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-400/80"></div>
                    <div className="w-3 h-3 rounded-full bg-emerald-400/80"></div>
                    <span className="text-xs font-mono text-slate-400 ml-2">salesmind_live_telemetry.ts</span>
                  </div>
                  <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded-md flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                    Live Walk-Forward Fit
                  </span>
                </div>

                {/* Animated Trend Metrics */}
                <div className="grid grid-cols-3 gap-3 mb-5">
                  <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Forecasted Run-Rate</span>
                    <span className="text-lg font-bold text-white">$142,850</span>
                    <span className="text-[10px] text-emerald-400 flex items-center gap-0.5 mt-0.5">
                      <TrendingUp className="w-3 h-3" /> +14.2% YoY
                    </span>
                  </div>
                  <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Model WAPE Fit</span>
                    <span className="text-lg font-bold text-cyan-300">92.4%</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">Auto-ARIMA (7d)</span>
                  </div>
                  <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Anomaly Filter</span>
                    <span className="text-lg font-bold text-emerald-400">0 Spike Alerts</span>
                    <span className="text-[10px] text-slate-400 block mt-0.5">|Z| &le; 2.5 Normal</span>
                  </div>
                </div>

                {/* SVG Visual Canvas with animated curve and glowing data points */}
                <div className="relative h-48 w-full">
                  <svg className="w-full h-full overflow-visible" viewBox="0 0 500 160">
                    <defs>
                      <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
                      </linearGradient>
                      <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#3b82f6" />
                        <stop offset="50%" stopColor="#06b6d4" />
                        <stop offset="100%" stopColor="#10b981" />
                      </linearGradient>
                    </defs>

                    {/* Background Grid Lines */}
                    <line x1="0" y1="40" x2="500" y2="40" stroke="#1e293b" strokeDasharray="3 3" />
                    <line x1="0" y1="80" x2="500" y2="80" stroke="#1e293b" strokeDasharray="3 3" />
                    <line x1="0" y1="120" x2="500" y2="120" stroke="#1e293b" strokeDasharray="3 3" />

                    {/* Gradient Area Fill */}
                    <path
                      d="M 20 130 Q 80 110 130 90 T 240 70 T 350 45 T 480 30 L 480 150 L 20 150 Z"
                      fill="url(#areaGradient)"
                      className="opacity-70"
                    />

                    {/* Animated Line Trend */}
                    <path
                      d="M 20 130 Q 80 110 130 90 T 240 70 T 350 45 T 480 30"
                      fill="none"
                      stroke="url(#lineGradient)"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      className="animate-draw-path"
                    />

                    {/* Projected Confidence Horizon (Dashed) */}
                    <path
                      d="M 350 45 Q 410 35 480 30"
                      fill="none"
                      stroke="#38bdf8"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                      className="opacity-90"
                    />

                    {/* Interactive Animated Nodes */}
                    {[
                      { cx: 20, cy: 130, label: 'W1' },
                      { cx: 130, cy: 90, label: 'W2' },
                      { cx: 240, cy: 70, label: 'W3' },
                      { cx: 350, cy: 45, label: 'W4' },
                      { cx: 480, cy: 30, label: 'W5 (Forecast)' }
                    ].map((pt, i) => (
                      <g key={i}>
                        <circle
                          cx={pt.cx}
                          cy={pt.cy}
                          r="6"
                          className="fill-slate-900 stroke-cyan-400 stroke-2"
                        />
                        <circle
                          cx={pt.cx}
                          cy={pt.cy}
                          r="3"
                          className="fill-cyan-300 animate-ping opacity-75"
                        />
                      </g>
                    ))}
                  </svg>
                </div>

                {/* Subtitle Telemetry Bar */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-3 border-t border-slate-800/80 font-mono">
                  <span>Horizon: 7 Days Forward</span>
                  <span>Confidence Bounds: 85% - 115%</span>
                  <span className="text-emerald-400">Deterministic Ledger</span>
                </div>
              </div>

              {/* Floating Glassmorphic Auxiliary Card 1 */}
              <div className="absolute -bottom-6 -left-6 bg-slate-900/90 backdrop-blur-md p-3.5 rounded-xl border border-blue-500/30 shadow-xl hidden sm:flex items-center gap-3 animate-float-card z-20">
                <div className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">
                  <LineChart className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-mono">Walk-Forward Engine</span>
                  <span className="text-xs font-bold text-white">Seasonal Naive & ARIMA</span>
                </div>
              </div>

              {/* Floating Glassmorphic Auxiliary Card 2 */}
              <div className="absolute -top-6 -right-6 bg-slate-900/90 backdrop-blur-md p-3.5 rounded-xl border border-cyan-500/30 shadow-xl hidden sm:flex items-center gap-3 animate-float-card-reverse z-20">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">
                  <Zap className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-mono">Demand Velocity</span>
                  <span className="text-xs font-bold text-emerald-300">+18.4% WoW Spike Shield</span>
                </div>
              </div>

            </div>
          </div>
        </div>

        {/* =========================================================================
            FEATURE VALUE PROPOSITIONS (Phase 2 Grid)
            ========================================================================= */}
        <div className={`mt-14 grid grid-cols-1 md:grid-cols-3 gap-5 transition-all duration-700 delay-200 ${
          animStage >= 7 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        }`}>
          <div className="bg-slate-900/50 backdrop-blur-md p-5 rounded-2xl border border-slate-800/80 hover:border-blue-500/40 transition">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3">
              <BarChart3 className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white mb-1">Empirical Ledger Precision</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              COUNT(DISTINCT order_id) precision with RFC 4180 verified exports and zero fabricated synthetic numbers.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-md p-5 rounded-2xl border border-slate-800/80 hover:border-cyan-500/40 transition">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mb-3">
              <Activity className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white mb-1">Dual-Model Walk-Forward Lab</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Benchmark Seasonal Naive vs Auto-ARIMA with chronological split horizons, WAPE, MAE, and RMSE tracking.
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-md p-5 rounded-2xl border border-slate-800/80 hover:border-teal-500/40 transition">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center mb-3">
              <Brain className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-bold text-white mb-1">Autonomous Diagnostics</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Dynamic Gaussian Z-Score anomaly scans, demand elasticity scenario simulations, and Gemini Pro advisory.
            </p>
          </div>
        </div>
      </main>

      {/* =========================================================================
          FOOTER
          ========================================================================= */}
      <footer className="relative z-10 max-w-7xl w-full mx-auto px-6 py-6 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-3">
        <p>&copy; {new Date().getFullYear()} SalesMind AI. All rights reserved. Production-grade Sales Intelligence SaaS.</p>
        <div className="flex items-center gap-6">
          <Link href="/login" className="hover:text-slate-300 transition">Sign In</Link>
          <Link href="/login?mode=register" className="hover:text-slate-300 transition">Register</Link>
          <button onClick={() => handleGetStarted('register')} className="text-cyan-400 hover:underline">
            Launch Platform &rarr;
          </button>
        </div>
      </footer>
    </div>
  )
}
