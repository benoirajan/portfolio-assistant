'use client'

import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts'
import type { PerformanceMetrics } from '@/lib/types'

interface Props { metrics: PerformanceMetrics }

function MetricCard({ label, value, help }: { label: string; value: string; help?: string }) {
  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg px-4 py-3" title={help}>
      <p className="text-xs text-[var(--muted)] mb-1">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  )
}

export default function PerformanceTab({ metrics }: Props) {
  const beta = metrics.portfolio_beta ?? 1
  const betaColor = beta < 0.85 ? 'var(--green)' : beta <= 1.15 ? 'var(--yellow)' : 'var(--red)'
  const gaugeData = [{ name: 'beta', value: Math.min(beta / 2, 1) * 100, fill: betaColor }]

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="XIRR" value={`${metrics.xirr_percentage.toFixed(2)}%`} help="Annualised internal rate of return" />
        <MetricCard label="Sharpe ratio" value={metrics.sharpe_ratio.toFixed(2)} help="Risk-adjusted return above ~7.1% risk-free rate" />
        <MetricCard label="Sortino ratio" value={metrics.sortino_ratio.toFixed(2)} help="Return adjusted for downside risk only" />
        <MetricCard label="Weighted P/E" value={`${metrics.weighted_pe.toFixed(1)}x`} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4">
          <p className="text-sm font-medium mb-2">Portfolio Beta vs Nifty 50</p>
          <ResponsiveContainer width="100%" height={200}>
            <RadialBarChart cx="50%" cy="100%" innerRadius="60%" outerRadius="100%" startAngle={180} endAngle={0} data={gaugeData}>
              <RadialBar dataKey="value" cornerRadius={6} background={{ fill: 'var(--border)' }} />
            </RadialBarChart>
          </ResponsiveContainer>
          <p className="text-center text-2xl font-bold mt-[-2rem]" style={{ color: betaColor }}>{beta.toFixed(2)}</p>
          <p className="text-center text-xs text-[var(--muted)] mt-1">
            {beta < 0.85 ? 'Low volatility' : beta <= 1.15 ? 'Market-aligned' : 'High volatility'}
          </p>
        </div>

        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4 flex flex-col gap-3">
          <p className="text-sm font-medium">Valuation matrix</p>
          {[
            { label: 'Weighted portfolio ROE', value: `${metrics.weighted_roe.toFixed(1)}%` },
            { label: 'Herfindahl concentration index', value: metrics.herfindahl_index.toLocaleString('en-IN', { maximumFractionDigits: 0 }), note: '< 1,500 = diversified' },
            { label: 'Risk classification', value: metrics.risk_profile_tag },
          ].map((r) => (
            <div key={r.label} className="flex justify-between items-center border-b border-[var(--border)] pb-2 last:border-0 last:pb-0">
              <span className="text-sm text-[var(--muted)]">{r.label}</span>
              <span className="text-sm font-medium">{r.value}{r.note && <span className="text-xs text-[var(--muted)] ml-1">({r.note})</span>}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
