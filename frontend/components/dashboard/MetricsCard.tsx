import React from 'react'

interface MetricsCardProps {
  title: string
  value: number | string
  icon: React.ReactNode
  unit?: string
  trend?: {
    value: number
    direction: 'up' | 'down'
  }
}

export function MetricsCard({ title, value, icon, unit, trend }: MetricsCardProps) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <div className="mt-3 flex items-baseline gap-2">
            <p className="text-3xl font-semibold text-slate-900">{value}</p>
            {unit && <span className="text-sm text-slate-400">{unit}</span>}
          </div>
          {trend && (
            <p
              className={`mt-3 text-sm ${
                trend.direction === 'up' ? 'text-emerald-600' : 'text-rose-600'
              }`}
            >
              {trend.direction === 'up' ? '↑' : '↓'} {trend.value}%
            </p>
          )}
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-lg font-semibold text-white">
          {icon}
        </div>
      </div>
    </div>
  )
}
