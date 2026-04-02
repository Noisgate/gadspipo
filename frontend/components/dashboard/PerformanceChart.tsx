'use client'

import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface ChartDataPoint {
  date: string
  impressions?: number
  clicks?: number
  conversions?: number
  cost?: number
  roas?: number
}

interface PerformanceChartProps {
  data: ChartDataPoint[]
  title: string
  lines?: ('impressions' | 'clicks' | 'conversions' | 'cost' | 'roas')[]
}

export function PerformanceChart({ data, title, lines = ['clicks', 'conversions'] }: PerformanceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 h-80 flex items-center justify-center">
        <p className="text-gray-500">Nenhum dado disponível</p>
      </div>
    )
  }

  const colorMap = {
    impressions: '#8b5cf6',
    clicks: '#0ea5e9',
    conversions: '#10b981',
    cost: '#ef4444',
    roas: '#f59e0b',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          {lines.includes('impressions') && (
            <Line
              type="monotone"
              dataKey="impressions"
              stroke={colorMap.impressions}
              dot={false}
              name="Impressões"
            />
          )}
          {lines.includes('clicks') && (
            <Line
              type="monotone"
              dataKey="clicks"
              stroke={colorMap.clicks}
              dot={false}
              name="Cliques"
            />
          )}
          {lines.includes('conversions') && (
            <Line
              type="monotone"
              dataKey="conversions"
              stroke={colorMap.conversions}
              dot={false}
              name="Conversões"
            />
          )}
          {lines.includes('cost') && (
            <Line
              type="monotone"
              dataKey="cost"
              stroke={colorMap.cost}
              dot={false}
              name="Custo (R$)"
            />
          )}
          {lines.includes('roas') && (
            <Line
              type="monotone"
              dataKey="roas"
              stroke={colorMap.roas}
              dot={false}
              name="ROAS"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
