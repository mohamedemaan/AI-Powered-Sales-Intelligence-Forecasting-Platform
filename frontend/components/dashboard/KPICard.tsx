import React from 'react'
import { TrendingUp, TrendingDown, HelpCircle } from 'lucide-react'

interface KPICardProps {
  title: string
  value: string | number
  trend?: string
  subtitle?: string
  tooltip?: string
  isDanger?: boolean
  icon?: React.ReactNode
}

export default function KPICard({
  title,
  value,
  trend,
  subtitle,
  tooltip,
  isDanger = false,
  icon
}: KPICardProps) {
  const isPositive = trend && trend.startsWith('+')
  const isNegative = trend && trend.startsWith('-')

  return (
    <div className="bg-surface p-5 rounded-xl border border-slate-700/80 hover:border-slate-600 transition shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-1.5 text-xs font-medium text-slate-400">
            <span>{title}</span>
            {tooltip && (
              <span className="cursor-help text-slate-500 hover:text-slate-300" title={tooltip}>
                <HelpCircle className="w-3.5 h-3.5 inline" />
              </span>
            )}
          </div>
          {icon && <div className="text-slate-400">{icon}</div>}
        </div>

        <div className="flex items-baseline justify-between gap-2">
          <span className="text-2xl font-bold tracking-tight text-white">{value}</span>
          
          {trend && (
            <div
              className={`flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
                isDanger
                  ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                  : isPositive
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : isNegative
                  ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                  : 'bg-slate-800 text-slate-300 border border-slate-700'
              }`}
            >
              {isPositive && <TrendingUp className="w-3 h-3 mr-1" />}
              {isNegative && <TrendingDown className="w-3 h-3 mr-1" />}
              {trend}
            </div>
          )}
        </div>
      </div>

      {subtitle && (
        <p className="text-[11px] text-slate-400 mt-2.5 pt-2 border-t border-slate-800/80">
          {subtitle}
        </p>
      )}
    </div>
  )
}
