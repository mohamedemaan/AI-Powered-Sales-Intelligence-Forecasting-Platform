import React from 'react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-900 text-white font-sans selection:bg-blue-500/30">
      {/* Navigation */}
      <nav className="flex justify-between items-center p-6 max-w-6xl mx-auto">
        <div className="text-2xl font-bold tracking-tight text-white">SalesIntel<span className="text-blue-500">.ai</span></div>
        <div className="space-x-8 text-sm font-medium">
          <a href="#features" className="hover:text-blue-400 transition-colors">Features</a>
          <a href="#pricing" className="hover:text-blue-400 transition-colors">Pricing</a>
          <a href="/login" className="hover:text-blue-400 transition-colors">Sign In</a>
          <a href="/register" className="bg-blue-600 px-5 py-2.5 rounded-full hover:bg-blue-500 transition-all shadow-[0_0_15px_rgba(37,99,235,0.4)]">Get Started</a>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-4xl mx-auto text-center pt-32 pb-20">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight">
          Predict demand.<br/>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            Never stock out again.
          </span>
        </h1>
        <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
          The autonomous Sales Intelligence Platform that learns your business, spots anomalies, and makes inventory decisions before you even realize there's a problem.
        </p>
        <div className="flex justify-center gap-4">
          <button className="bg-blue-600 text-white px-8 py-4 rounded-full text-lg font-semibold hover:bg-blue-500 transition-all shadow-[0_0_20px_rgba(37,99,235,0.4)] hover:shadow-[0_0_30px_rgba(37,99,235,0.6)] hover:-translate-y-1">
            Start Free Trial
          </button>
          <button className="bg-slate-800 text-white px-8 py-4 rounded-full text-lg font-semibold border border-slate-700 hover:bg-slate-700 transition-all">
            Book a Demo
          </button>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="max-w-6xl mx-auto py-24 px-6">
        <h2 className="text-3xl font-bold text-center mb-16">Simple, Usage-based Pricing</h2>
        <div className="grid md:grid-cols-3 gap-8">
          
          {/* Free Tier */}
          <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
            <h3 className="text-xl font-semibold mb-2">Starter</h3>
            <div className="text-4xl font-bold mb-6">$0<span className="text-lg text-slate-400 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8 text-slate-300">
              <li>✓ 1 User Seat</li>
              <li>✓ 10 ML Forecasts/mo</li>
              <li>✓ 7-Day Data History</li>
            </ul>
            <button className="w-full py-3 rounded-lg border border-slate-600 hover:bg-slate-700 transition-colors">Current Plan</button>
          </div>

          {/* Pro Tier */}
          <div className="bg-gradient-to-b from-blue-900/50 to-slate-800 p-8 rounded-2xl border border-blue-500/50 relative transform md:-translate-y-4">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-semibold">Most Popular</div>
            <h3 className="text-xl font-semibold mb-2">Pro</h3>
            <div className="text-4xl font-bold mb-6">$49<span className="text-lg text-slate-400 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8 text-slate-300">
              <li>✓ 5 User Seats</li>
              <li>✓ 100 ML Forecasts/mo</li>
              <li>✓ AI Copilot Access</li>
              <li>✓ Slack Alerts</li>
            </ul>
            <button className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 font-medium transition-colors">Upgrade to Pro</button>
          </div>

          {/* Business Tier */}
          <div className="bg-slate-800 p-8 rounded-2xl border border-slate-700">
            <h3 className="text-xl font-semibold mb-2">Business</h3>
            <div className="text-4xl font-bold mb-6">$199<span className="text-lg text-slate-400 font-normal">/mo</span></div>
            <ul className="space-y-4 mb-8 text-slate-300">
              <li>✓ 20 User Seats</li>
              <li>✓ Unlimited Forecasts</li>
              <li>✓ Custom Model Retraining</li>
              <li>✓ Priority Support</li>
            </ul>
            <button className="w-full py-3 rounded-lg border border-slate-600 hover:bg-slate-700 transition-colors">Contact Sales</button>
          </div>

        </div>
      </section>
    </div>
  )
}
