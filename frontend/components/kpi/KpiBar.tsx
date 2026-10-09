import type { PortfolioSummary, PerformanceMetrics } from '@/lib/types'

interface Props {
  summary: PortfolioSummary
  metrics: PerformanceMetrics
}

function Card({
  label,
  value,
  sub,
  subColor,
}: {
  label: string
  value: string
  sub?: string
  subColor?: string
}) {
  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 flex flex-col justify-between shadow-xs transition-colors">
      <p className="text-[11px] sm:text-xs text-[var(--muted)] font-medium truncate">{label}</p>
      <p className="text-base sm:text-lg font-bold tracking-tight text-[var(--text)] mt-0.5 truncate">{value}</p>
      {sub ? (
        <p className={`text-[11px] font-medium mt-0.5 truncate ${subColor ?? 'text-[var(--muted)]'}`}>{sub}</p>
      ) : (
        <div className="h-4" />
      )}
    </div>
  )
}

export default function KpiBar({ summary, metrics }: Props) {
  const totalPnl = summary?.total_pnl ?? 0
  const pnlColor = totalPnl >= 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'
  const pnlSign = totalPnl >= 0 ? '+' : ''
  const pnlPct = summary?.total_pnl_percentage ?? 0
  const xirr = metrics?.xirr_percentage ?? 0
  const beta = metrics?.portfolio_beta ?? 1
  const riskTag = metrics?.risk_profile_tag ?? '—'

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3 px-4 sm:px-6 py-3 sm:py-4">
      <Card
        label="Total Invested"
        value={`₹${(summary?.total_investment ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
      />
      <Card
        label="Current Value"
        value={`₹${(summary?.current_value ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
      />
      <Card
        label="Overall P&L"
        value={`₹${totalPnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
        sub={`${pnlSign}${pnlPct.toFixed(2)}%`}
        subColor={pnlColor}
      />
      <Card
        label="Portfolio XIRR"
        value={`${xirr.toFixed(2)}%`}
        sub="Annualised"
      />
      <Card
        label="Portfolio Beta"
        value={beta.toFixed(2)}
        sub="vs Nifty 50"
      />
      <Card
        label="Risk Profile"
        value={riskTag}
        sub="SEBI Class"
      />
    </div>
  )
}
