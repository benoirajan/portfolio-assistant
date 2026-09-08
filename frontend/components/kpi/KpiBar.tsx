import type { PortfolioSummary, PerformanceMetrics } from '@/lib/types'

interface Props {
  summary: PortfolioSummary
  metrics: PerformanceMetrics
}

function Card({ label, value, sub, subColor }: { label: string; value: string; sub?: string; subColor?: string }) {
  return (
    <div className="flex-1 min-w-[130px] bg-[var(--surface)] border border-[var(--border)] rounded-lg px-4 py-3">
      <p className="text-xs text-[var(--muted)] mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {sub && <p className={`text-xs mt-0.5 ${subColor ?? 'text-[var(--muted)]'}`}>{sub}</p>}
    </div>
  )
}

export default function KpiBar({ summary, metrics }: Props) {
  const pnlColor = summary.total_pnl >= 0 ? 'text-[var(--green)]' : 'text-[var(--red)]'
  const pnlSign = summary.total_pnl >= 0 ? '+' : ''

  return (
    <div className="flex flex-wrap gap-3 px-6 py-4">
      <Card label="Total invested" value={`₹${summary.total_investment.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} />
      <Card label="Current value" value={`₹${summary.current_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} />
      <Card
        label="Overall P&L"
        value={`₹${summary.total_pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
        sub={`${pnlSign}${summary.total_pnl_percentage.toFixed(2)}%`}
        subColor={pnlColor}
      />
      <Card label="Portfolio XIRR" value={`${metrics.xirr_percentage.toFixed(2)}%`} />
      <Card label="Portfolio Beta" value={metrics.portfolio_beta.toFixed(2)} sub="vs Nifty 50" />
      <Card label="Risk profile" value={metrics.risk_profile_tag} />
    </div>
  )
}
