'use client'

import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Area,
  ComposedChart,
  ResponsiveContainer
} from 'recharts'

export default function ForecastChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-80 w-full flex items-center justify-center text-slate-500">
        <p>No forecast data available. Select a product and run an analysis to visualize results.</p>
      </div>
    )
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 15, right: 25, left: -10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={{ stroke: '#475569' }}
          />
          <YAxis
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={{ stroke: '#475569' }}
            tickFormatter={(val) => `${val}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '0.75rem',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)',
              fontSize: '12px'
            }}
            labelStyle={{ color: '#f8fafc', fontWeight: 600, marginBottom: '4px' }}
            formatter={(value: any, name: string) => {
              if (value == null) return ['N/A', name]
              if (name === 'actual') return [`${value} units`, 'Actual Sales']
              if (name === 'forecast') return [`${value} units`, 'Forecast Demand']
              if (name === 'lower') return [`${value} units`, 'Lower Bound (85%)']
              if (name === 'upper') return [`${value} units`, 'Upper Bound (115%)']
              return [value, name]
            }}
          />

          {/* Confidence Interval (85% - 115%) */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#3b82f6"
            fillOpacity={0.12}
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#0f172a"
            fillOpacity={1}
            isAnimationActive={false}
          />

          {/* Actual Observations: Emerald solid line + dots */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#10b981"
            strokeWidth={2.5}
            dot={{ r: 3, fill: '#10b981', stroke: '#064e3b', strokeWidth: 1 }}
            activeDot={{ r: 5 }}
            connectNulls={false}
            name="actual"
          />

          {/* Forecasted Trajectory: Blue dashed line */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#3b82f6"
            strokeWidth={2.5}
            strokeDasharray="4 4"
            dot={{ r: 3, fill: '#3b82f6', stroke: '#1e3a8a', strokeWidth: 1 }}
            activeDot={{ r: 5 }}
            connectNulls={false}
            name="forecast"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
