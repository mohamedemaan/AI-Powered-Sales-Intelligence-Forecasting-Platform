import os

backend_files = {
    "backend/app/ml/explainability.py": """import pandas as pd
import numpy as np

def generate_explanations(df: pd.DataFrame, model, predictions) -> dict:
    # Simplified mock explainability (In production, use SHAP with tree models)
    # We analyze the feature variance to determine drivers
    
    recent_data = df.tail(7).copy()
    avg_stock = recent_data['available_stock'].mean() if 'available_stock' in recent_data else 0
    avg_discount = recent_data['discount_pct'].mean() if 'discount_pct' in recent_data else 0
    
    drivers = []
    if avg_discount > 0:
        drivers.append({"factor": "Discount", "impact": "Positive", "weight": 0.45})
    if avg_stock < 50:
        drivers.append({"factor": "Low Stock", "impact": "Negative", "weight": -0.30})
        
    drivers.append({"factor": "Recent Trend", "impact": "Positive", "weight": 0.25})
    
    text = "Sales prediction is primarily driven by "
    text += ", ".join([d['factor'] for d in drivers])
    
    return {
        "summary": text,
        "drivers": drivers
    }
""",

    "backend/app/ml/anomaly.py": """import pandas as pd
import numpy as np

def detect_anomalies(df: pd.DataFrame, target_col='units_sold', threshold=2.5) -> pd.DataFrame:
    if df.empty or len(df) < 14:
        df['is_anomaly'] = False
        df['anomaly_severity'] = 'None'
        return df
        
    mean = df[target_col].mean()
    std = df[target_col].std()
    
    # Z-Score method
    df['z_score'] = (df[target_col] - mean) / (std + 1e-9)
    
    conditions = [
        (df['z_score'].abs() >= 3.5),
        (df['z_score'].abs() >= 2.5),
        (df['z_score'].abs() >= 1.5)
    ]
    choices = ['High', 'Medium', 'Low']
    
    df['is_anomaly'] = df['z_score'].abs() >= threshold
    df['anomaly_severity'] = np.select(conditions, choices, default='None')
    
    return df
""",

    "backend/app/services/simulation.py": """import pandas as pd
from app.ml.baseline import BaselineModel

def simulate_scenario(base_df: pd.DataFrame, price_change: float, discount: float, demand_multiplier: float):
    # Create a copy to simulate
    sim_df = base_df.copy()
    
    # Apply user inputs
    if 'price' in sim_df:
        sim_df['price'] = sim_df['price'] * (1 + price_change/100)
    if 'discount_pct' in sim_df:
        sim_df['discount_pct'] = discount
        
    # Simulate demand impact (simplified elasticity)
    elasticity_factor = 1 + (discount / 100 * 1.5) - (price_change / 100 * 0.8)
    total_multiplier = demand_multiplier * elasticity_factor
    
    sim_df['units_sold'] = sim_df['units_sold'] * total_multiplier
    
    # Re-run a baseline model on simulated data
    model = BaselineModel().fit(sim_df)
    sim_preds = model.predict(7)
    
    return {
        "simulated_predictions": sim_preds.tolist(),
        "projected_revenue": (sum(sim_preds) * sim_df['price'].iloc[-1] * (1 - discount/100)) if 'price' in sim_df else 0
    }
""",

    "backend/app/api/v1/endpoints/analytics.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db

router = APIRouter()

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    # Mocking DB aggregations for dashboard
    return {
        "revenue": 125000,
        "revenue_growth": 12.5,
        "active_predictions": 45,
        "anomalies_detected": 3
    }

@router.get("/anomalies")
def get_anomalies(sku: str, db: Session = Depends(get_db)):
    from app.pipelines.etl import extract_for_features
    from app.ml.anomaly import detect_anomalies
    
    df = extract_for_features(db, sku)
    if len(df) == 0:
        return []
        
    df = detect_anomalies(df)
    anomalies = df[df['is_anomaly'] == True]
    
    # Return JSON records
    return anomalies[['date', 'units_sold', 'anomaly_severity', 'z_score']].tail(10).to_dict(orient='records')

@router.post("/simulate")
def run_simulation(sku: str, price_change: float = 0, discount: float = 0, demand_mult: float = 1.0, db: Session = Depends(get_db)):
    from app.pipelines.etl import extract_for_features
    from app.services.simulation import simulate_scenario
    
    df = extract_for_features(db, sku)
    if len(df) == 0:
        return {"error": "No data"}
        
    result = simulate_scenario(df, price_change, discount, demand_mult)
    return result

@router.post("/copilot")
def ask_copilot(query: str, sku: str = None, db: Session = Depends(get_db)):
    # Simulated LLM Agent Intelligence Layer
    # In production, this passes context to an LLM like Gemini
    
    if "drop" in query.lower():
        return {
            "answer": "Sales dropped by 15% last week primarily due to a localized stock-out event and the end of the holiday promotion.",
            "evidence": {"stock_level": "0 for 2 days", "discount": "Dropped from 20% to 0%"},
            "recommendation": "Ensure safety stock is increased by 10% before next promotional event."
        }
    return {
        "answer": "Based on current trends, sales are stable. The forecasting model anticipates a 5% growth next month.",
        "evidence": {"trend": "Positive", "confidence": "85%"},
        "recommendation": "Maintain current pricing strategy."
    }
"""
}

frontend_files = {
    "frontend/package.json": """{
  "name": "sales-intel-dashboard",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18",
    "react-dom": "^18",
    "recharts": "^3.0.0",
    "lucide-react": "^0.290.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "postcss": "^8",
    "autoprefixer": "^10.0.1"
  }
}
""",

    "frontend/tsconfig.json": """{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
""",

    "frontend/tailwind.config.js": """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f172a',
        surface: '#1e293b',
        primary: '#3b82f6',
        accent: '#10b981',
        danger: '#ef4444'
      }
    },
  },
  plugins: [],
}
""",

    "frontend/postcss.config.js": """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
""",

    "frontend/app/layout.tsx": """import './globals.css'
import { ReactNode } from 'react'

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-background text-slate-200 min-h-screen">
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar */}
          <aside className="w-64 bg-surface border-r border-slate-700 flex flex-col p-4">
            <h1 className="text-xl font-bold text-white mb-8">Sales Intel AI</h1>
            <nav className="flex flex-col gap-4">
              <a href="/" className="hover:text-primary transition-colors">Overview</a>
              <a href="/forecast" className="hover:text-primary transition-colors">Forecast Lab</a>
              <a href="/anomalies" className="hover:text-primary transition-colors">Anomalies</a>
              <a href="/copilot" className="hover:text-primary transition-colors">AI Copilot</a>
            </nav>
          </aside>
          
          {/* Main Content */}
          <main className="flex-1 overflow-y-auto p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
""",

    "frontend/app/globals.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  color: rgb(var(--foreground-rgb));
  background: rgb(var(--background-start-rgb));
}
""",

    "frontend/app/page.tsx": """import KPICard from '../components/dashboard/KPICard'
import ForecastChart from '../components/charts/ForecastChart'

export default function DashboardOverview() {
  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-3xl font-bold text-white">Global Overview</h2>
        <p className="text-slate-400">Real-time intelligence and forecasting.</p>
      </header>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <KPICard title="Projected Revenue" value="$125,000" trend="+12.5%" />
        <KPICard title="Active Predictions" value="45 SKUs" trend="+3" />
        <KPICard title="Anomalies Detected" value="3" trend="-2" isDanger />
        <KPICard title="Model Accuracy (WAPE)" value="92.4%" trend="+1.2%" />
      </div>

      {/* Main Chart */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">Actual vs Forecast (Confidence Bounds)</h3>
        <ForecastChart />
      </div>
    </div>
  )
}
""",

    "frontend/components/dashboard/KPICard.tsx": """export default function KPICard({ title, value, trend, isDanger = false }: any) {
  const trendColor = isDanger ? 'text-danger' : 'text-accent'
  return (
    <div className="bg-surface p-6 rounded-xl border border-slate-700 flex flex-col gap-2">
      <span className="text-sm text-slate-400">{title}</span>
      <div className="flex items-end justify-between">
        <span className="text-3xl font-bold text-white">{value}</span>
        <span className={`text-sm font-medium ${trendColor}`}>{trend}</span>
      </div>
    </div>
  )
}
""",

    "frontend/components/charts/ForecastChart.tsx": """'use client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Area, ComposedChart, ResponsiveContainer } from 'recharts'

const data = [
  { date: 'Oct 1', actual: 120, forecast: null, lower: null, upper: null },
  { date: 'Oct 2', actual: 135, forecast: null, lower: null, upper: null },
  { date: 'Oct 3', actual: 125, forecast: 125, lower: 110, upper: 140 },
  { date: 'Oct 4', actual: null, forecast: 140, lower: 120, upper: 160 },
  { date: 'Oct 5', actual: null, forecast: 155, lower: 135, upper: 175 },
]

export default function ForecastChart() {
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis dataKey="date" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
          
          {/* Confidence Interval */}
          <Area type="monotone" dataKey="upper" stroke="none" fill="#3b82f6" fillOpacity={0.1} />
          <Area type="monotone" dataKey="lower" stroke="none" fill="#1e293b" fillOpacity={1} />
          
          {/* Lines */}
          <Line type="monotone" dataKey="actual" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="forecast" stroke="#3b82f6" strokeWidth={3} strokeDasharray="5 5" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
""",

    "frontend/app/copilot/page.tsx": """'use client'
import { useState } from 'react'

export default function CopilotPage() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState<any>(null)

  const askAI = async () => {
    // Mock API call to backend /api/v1/analytics/copilot
    setResponse({
      answer: "Sales dropped by 15% last week primarily due to a localized stock-out event.",
      evidence: { stock_level: "0 for 2 days" },
      recommendation: "Ensure safety stock is increased by 10%."
    })
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h2 className="text-3xl font-bold text-white">AI Copilot</h2>
      
      <div className="bg-surface p-6 rounded-xl border border-slate-700">
        <textarea 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about sales trends, anomalies, or risks..."
          className="w-full bg-background text-white p-4 rounded-lg border border-slate-600 focus:outline-none focus:border-primary h-32"
        />
        <div className="mt-4 flex justify-end">
          <button onClick={askAI} className="bg-primary text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-600 transition-colors">
            Ask Copilot
          </button>
        </div>
      </div>

      {response && (
        <div className="bg-blue-900/20 border border-blue-500/50 p-6 rounded-xl space-y-4">
          <h4 className="text-lg font-semibold text-blue-400">AI Analysis</h4>
          <p className="text-white text-lg">{response.answer}</p>
          
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="bg-surface p-4 rounded-lg">
              <span className="text-sm text-slate-400 block mb-1">Evidence</span>
              <code className="text-accent">{JSON.stringify(response.evidence)}</code>
            </div>
            <div className="bg-surface p-4 rounded-lg">
              <span className="text-sm text-slate-400 block mb-1">Recommendation</span>
              <span className="text-white">{response.recommendation}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
"""
}

def create_phase3():
    # Write Backend Files
    for filepath, content in backend_files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    # Update api.py to include analytics
    api_path = "backend/app/api/v1/api.py"
    if os.path.exists(api_path):
        with open(api_path, "r", encoding='utf-8') as f:
            content = f.read()
        if "analytics" not in content:
            with open(api_path, "a", encoding='utf-8') as f:
                f.write("\\nfrom app.api.v1.endpoints import analytics\\n")
                f.write("api_router.include_router(analytics.router, prefix='/analytics', tags=['analytics'])\\n")
                
    # Write Frontend Files
    for filepath, content in frontend_files.items():
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    create_phase3()
    print("Phase 3 setup (Backend AI + Frontend Next.js) completed successfully!")
