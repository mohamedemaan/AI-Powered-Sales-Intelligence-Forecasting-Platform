export default function Onboarding() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6">
      <div className="bg-slate-800 max-w-lg w-full p-10 rounded-2xl border border-slate-700 text-center">
        <h2 className="text-2xl font-bold text-white mb-4">Welcome to SalesIntel.ai</h2>
        <p className="text-slate-400 mb-8">Let's get your autonomous intelligence engine running.</p>
        
        <div className="space-y-4">
          <button className="w-full bg-blue-600 text-white py-4 rounded-xl font-medium hover:bg-blue-500 transition-all flex items-center justify-center gap-2">
            Upload Historical Sales Data (CSV)
          </button>
          <button className="w-full bg-slate-700 text-white py-4 rounded-xl font-medium hover:bg-slate-600 transition-all">
            Connect Shopify Integration
          </button>
        </div>
        
        <a href="/dashboard" className="block mt-6 text-sm text-slate-500 hover:text-white transition-colors">Skip for now, show me the demo dashboard</a>
      </div>
    </div>
  )
}
