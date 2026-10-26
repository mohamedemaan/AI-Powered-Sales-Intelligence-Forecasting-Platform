'use client'

import {
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ComposedChart,
  ResponsiveContainer,
  Legend
} from 'recharts'

interface TrendsChartProps {
  data: Array<{
    date: string
    revenue: number
    units_sold: number
    orders: number
    profit?: number | null
  }>
  metric: 'revenue' | 'units_sold' | 'both'
}

export default function TrendsChart({ data, metric = 'both' }: TrendsChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-72 w-full flex items-center justify-center text-slate-500">
        <p>No trend data available for the selected interval and filter.</p>
      </div>
    )
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 15, right: 20, left: -5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={{ stroke: '#475569' }}
          />
          <YAxis
            yAxisId="left"
            stroke="#38bdf8"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            tickLine={{ stroke: '#475569' }}
            tickFormatter={(val) => `$${val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val}`}
          />
          {metric === 'both' && (
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#a855f7"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={{ stroke: '#475569' }}
              tickFormatter={(val) => `${val}`}
            />
          )}

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
              if (name === 'Revenue ($)') return [`$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name]
              if (name === 'Profit ($)') return [`$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, name]
              return [Number(value).toLocaleString(), name]
            }}
          />
          <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />

          {(metric === 'revenue' || metric === 'both') && (
            <Bar
              yAxisId="left"
              dataKey="revenue"
              name="Revenue ($)"
              fill="#38bdf8"
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
              opacity={0.85}
            />
          )}

          {(metric === 'units_sold' || metric === 'both') && (
            <Line
              yAxisId={metric === 'both' ? 'right' : 'left'}
              type="monotone"
              dataKey="units_sold"
              name="Units Sold"
              stroke="#a855f7"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#a855f7' }}
              activeDot={{ r: 5 }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}

