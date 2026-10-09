'use client'

import type { PerformanceMetrics } from '@/lib/types'

interface Props {
  metrics: PerformanceMetrics
}

function MetricCard({
  label,
  value,
  help,
}: {
  label: string
  value: string
  help?: string
}) {
  return (
    <div
      className="bg-[var(--surface)] border border-[var(--border)] rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 shadow-xs"
      title={help}
    >
      <p className="text-[11px] sm:text-xs text-[var(--muted)] mb-1 truncate">{label}</p>
      <p className="text-lg sm:text-xl font-bold tracking-tight text-[var(--text)]">{value}</p>
      {help && (
        <p className="text-[10px] text-[var(--muted)] mt-1 line-clamp-1 hidden sm:block">
          {help}
        </p>
      )}
    </div>
  )
}

function BetaSvgGauge({ beta, betaColor }: { beta: number; betaColor: string }) {
  // Clamped ratio between 0 and 2.0 (1.0 = Nifty benchmark)
  const normalized = Math.min(Math.max(beta, 0), 2.0)
  const ratio = normalized / 2.0
  const circumference = Math.PI * 70 // approx 219.91
  const strokeDashoffset = circumference * (1 - ratio)

  return (
    <div className="flex flex-col items-center justify-center py-2">
      <div className="relative w-full max-w-[220px] aspect-[2/1.3] flex items-center justify-center">
        <svg viewBox="0 0 200 120" className="w-full h-full overflow-visible">
          {/* Background arc */}
          <path
            d="M 30 100 A 70 70 0 0 1 170 100"
            fill="none"
            stroke="var(--border)"
            strokeWidth="14"
            strokeLinecap="round"
          />
          {/* Progress arc */}
          <path
            d="M 30 100 A 70 70 0 0 1 170 100"
            fill="none"
            stroke={betaColor}
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-700 ease-out"
          />
          {/* Center text score */}
          <text
            x="100"
            y="92"
            textAnchor="middle"
            fill={betaColor}
            className="text-3xl font-extrabold"
            style={{ fontSize: '28px', fontWeight: '800' }}
          >
            {beta.toFixed(2)}
          </text>
          {/* Min / Max labels */}
          <text x="28" y="116" fill="var(--muted)" fontSize="9" textAnchor="middle">0.0</text>
          <text x="100" y="116" fill="var(--muted)" fontSize="9" textAnchor="middle">1.0 (Nifty)</text>
          <text x="172" y="116" fill="var(--muted)" fontSize="9" textAnchor="middle">2.0+</text>
        </svg>
      </div>

      <div className="text-center mt-3">
        <span
          className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold"
          style={{
            color: betaColor,
            backgroundColor: `color-mix(in srgb, ${betaColor} 15%, transparent)`,
          }}
        >
          {beta < 0.85 ? 'Low Volatility Defensive' : beta <= 1.15 ? 'Market-Aligned (Balanced)' : 'High Volatility Aggressive'}
        </span>
        <p className="text-[11px] text-[var(--muted)] mt-1.5">
          Measures systemic risk and co-movement relative to NIFTY 50 index.
        </p>
      </div>
    </div>
  )
}

export default function PerformanceTab({ metrics }: Props) {
  const beta = metrics?.portfolio_beta ?? 1
  const betaColor = beta < 0.85 ? 'var(--green)' : beta <= 1.15 ? 'var(--yellow)' : 'var(--red)'

  const xirr = metrics?.xirr_percentage ?? 0
  const sharpe = metrics?.sharpe_ratio ?? 0
  const sortino = metrics?.sortino_ratio ?? 0
  const weightedPe = metrics?.weighted_pe ?? 0
  const weightedRoe = metrics?.weighted_roe ?? 0
  const hhi = metrics?.herfindahl_index ?? 0
  const riskTag = metrics?.risk_profile_tag ?? '—'

  return (
    <div className="flex flex-col gap-5 sm:gap-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 sm:gap-3">
        <MetricCard
          label="Portfolio XIRR"
          value={`${xirr.toFixed(2)}%`}
          help="Annualised internal rate of return based on actual cash flows"
        />
        <MetricCard
          label="Sharpe Ratio"
          value={sharpe.toFixed(2)}
          help="Excess return per unit of total risk above ~7.1% Indian risk-free rate"
        />
        <MetricCard
          label="Sortino Ratio"
          value={sortino.toFixed(2)}
          help="Excess return per unit of downside deviation only"
        />
        <MetricCard
          label="Weighted P/E"
          value={`${weightedPe.toFixed(1)}x`}
          help="Market-cap weighted Price-to-Earnings valuation multiple"
        />
      </div>

      {/* Beta Gauge & Valuation Matrix */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* Beta Gauge Card */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 sm:p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-[var(--text)]">Portfolio Beta vs Nifty 50</h4>
            <span className="text-xs text-[var(--muted)]">SEBI Benchmark</span>
          </div>

          <BetaSvgGauge beta={beta} betaColor={betaColor} />
        </div>

        {/* Valuation & Concentration Matrix */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 sm:p-5 flex flex-col justify-between gap-4">
          <div>
            <h4 className="text-sm font-semibold text-[var(--text)] mb-1">Valuation & Concentration Matrix</h4>
            <p className="text-xs text-[var(--muted)]">Quantitative factors evaluated across active holdings.</p>
          </div>

          <div className="flex flex-col gap-3 divide-y divide-[var(--border)]">
            <div className="flex justify-between items-center pt-2">
              <span className="text-xs sm:text-sm text-[var(--muted)]">Weighted Portfolio ROE</span>
              <span className="text-xs sm:text-sm font-semibold text-[var(--text)]">
                {weightedRoe.toFixed(1)}%
              </span>
            </div>

            <div className="flex justify-between items-center pt-3">
              <div>
                <span className="text-xs sm:text-sm text-[var(--muted)] block">Herfindahl Index (HHI)</span>
                <span className="text-[10px] text-[var(--muted)]">
                  {hhi < 1500 ? 'Well Diversified (<1500)' : hhi < 2500 ? 'Moderately Concentrated' : 'Highly Concentrated (>2500)'}
                </span>
              </div>
              <span className="text-xs sm:text-sm font-semibold text-[var(--text)]">
                {hhi.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </span>
            </div>

            <div className="flex justify-between items-center pt-3">
              <span className="text-xs sm:text-sm text-[var(--muted)]">SEBI Risk Classification</span>
              <span className="text-xs sm:text-sm font-semibold px-2 py-0.5 rounded-md bg-[var(--bg)] border border-[var(--border)] text-[var(--text)]">
                {riskTag}
              </span>
            </div>

            <div className="flex justify-between items-center pt-3">
              <span className="text-xs sm:text-sm text-[var(--muted)]">Risk-Free Rate Benchmark</span>
              <span className="text-xs sm:text-sm font-semibold text-[var(--text)]">
                7.10% (10Y G-Sec)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
