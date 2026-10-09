'use client'

import type { TaxAnalysis } from '@/lib/types'
import { Lock, Sparkles, ArrowUpCircle, CheckCircle2, AlertCircle } from 'lucide-react'

interface Props {
  tax?: TaxAnalysis | null
  isGated?: boolean
  onUpgradeClick?: () => void
}

const LTCG_LIMIT = 125000

export default function TaxTab({ tax, isGated = false, onUpgradeClick }: Props) {
  // If user is gated (FREE tier or 403 Forbidden), show high-conversion locked feature preview
  if (isGated) {
    return (
      <div className="flex flex-col gap-6 max-w-4xl mx-auto py-2">
        <div className="relative overflow-hidden bg-[var(--surface)] border border-amber-500/30 rounded-2xl p-6 sm:p-8 shadow-lg">
          {/* Subtle gradient background glow */}
          <div className="absolute -right-20 -top-20 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-amber-500/15 text-amber-500 flex items-center justify-center shrink-0">
                <Lock size={24} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg sm:text-xl font-bold text-[var(--text)]">
                    Tax-Loss Harvesting Engine
                  </h3>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-400 text-black">
                    PRO
                  </span>
                </div>
                <p className="text-xs text-[var(--muted)] mt-0.5">
                  Institutional capital gains optimization tailored for Indian equity portfolios.
                </p>
              </div>
            </div>

            {onUpgradeClick && (
              <button
                onClick={onUpgradeClick}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 bg-amber-400 hover:bg-amber-300 text-black font-semibold text-xs rounded-xl shadow-md transition-all cursor-pointer"
              >
                <ArrowUpCircle size={15} />
                <span>Upgrade to Pro (₹299/mo)</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)] flex flex-col gap-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text)]">
                <CheckCircle2 size={14} className="text-amber-500" />
                <span>Real-Time STCG (20%) & LTCG (12.5%)</span>
              </div>
              <p className="text-[11px] text-[var(--muted)]">
                Compliant with Indian Union Budget 2024 revisions. Automatically segregates holdings based on 365-day thresholds.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)] flex flex-col gap-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text)]">
                <CheckCircle2 size={14} className="text-amber-500" />
                <span>₹1.25 Lakh Exemption Tracker</span>
              </div>
              <p className="text-[11px] text-[var(--muted)]">
                Monitors your cumulative LTCG against Section 112A's ₹1,25,000 threshold to prevent unnecessary tax outgo.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)] flex flex-col gap-1.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text)]">
                <CheckCircle2 size={14} className="text-amber-500" />
                <span>March 31st Tax-Saving Trades</span>
              </div>
              <p className="text-[11px] text-[var(--muted)]">
                Uncovers unrealized loss candidates across holdings to offset taxable gains before fiscal year-end.
              </p>
            </div>
          </div>

          {/* Locked Preview Teaser */}
          <div className="relative rounded-xl border border-[var(--border)] bg-[var(--bg)] p-4 overflow-hidden select-none opacity-60">
            <div className="absolute inset-0 backdrop-blur-[2px] flex items-center justify-center z-10 bg-[var(--surface)]/40">
              <div className="text-center p-4">
                <Sparkles size={20} className="mx-auto text-amber-500 mb-1" />
                <p className="text-xs font-medium text-[var(--text)]">
                  Available exclusively to PRO & ELITE members
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
              <div className="p-2.5 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
                <div className="h-3 w-16 bg-[var(--border)] rounded mb-1" />
                <div className="h-5 w-24 bg-[var(--border)] rounded" />
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
                <div className="h-3 w-16 bg-[var(--border)] rounded mb-1" />
                <div className="h-5 w-24 bg-[var(--border)] rounded" />
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
                <div className="h-3 w-16 bg-[var(--border)] rounded mb-1" />
                <div className="h-5 w-24 bg-[var(--border)] rounded" />
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
                <div className="h-3 w-16 bg-[var(--border)] rounded mb-1" />
                <div className="h-5 w-24 bg-[var(--border)] rounded" />
              </div>
            </div>
            <div className="h-3 w-full bg-[var(--border)] rounded-full" />
          </div>
        </div>
      </div>
    )
  }

  // Active Unlocked View
  const netStcg = tax?.net_stcg ?? 0
  const stcgTax = tax?.stcg_tax_payable ?? 0
  const netLtcg = tax?.net_ltcg ?? 0
  const ltcgTax = tax?.ltcg_tax_payable ?? 0
  const ltcgUsed = tax?.ltcg_exemption_used ?? 0
  const candidates = tax?.harvestable_loss_candidates ?? []

  const exemptionPct = Math.min(1, ltcgUsed / LTCG_LIMIT)

  return (
    <div className="flex flex-col gap-5 sm:gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <p className="text-xs sm:text-sm text-[var(--muted)]">
          Optimise capital gains tax by harvesting unrealised losses before March 31st (Union Budget 2024 rules).
        </p>
        <span className="text-[11px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full w-fit">
          FY 2024-25 Rules Active
        </span>
      </div>

      {/* Tax metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 sm:gap-3">
        {[
          { label: 'Net STCG (<1 yr)', value: `₹${netStcg.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
          { label: 'STCG Tax (20%)', value: `₹${stcgTax.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
          { label: 'Net LTCG (>1 yr)', value: `₹${netLtcg.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
          { label: 'LTCG Tax (12.5%)', value: `₹${ltcgTax.toLocaleString('en-IN', { maximumFractionDigits: 0 })}` },
        ].map((c) => (
          <div key={c.label} className="bg-[var(--surface)] border border-[var(--border)] rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 shadow-xs">
            <p className="text-[11px] sm:text-xs text-[var(--muted)] mb-1 truncate">{c.label}</p>
            <p className="text-base sm:text-lg font-bold tracking-tight text-[var(--text)]">{c.value}</p>
          </div>
        ))}
      </div>

      {/* LTCG Annual Exemption Tracker */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 sm:p-5 shadow-xs">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs sm:text-sm font-semibold text-[var(--text)]">
            LTCG Annual Exemption (₹1.25 Lakh Limit)
          </p>
          <span className="text-xs font-semibold text-[var(--muted)]">
            {(exemptionPct * 100).toFixed(0)}% Utilised
          </span>
        </div>

        <div className="w-full bg-[var(--border)] rounded-full h-3 overflow-hidden">
          <div
            className="h-3 rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${exemptionPct * 100}%`,
              backgroundColor: exemptionPct >= 1 ? 'var(--red)' : 'var(--blue)',
            }}
          />
        </div>

        <div className="flex items-center justify-between text-xs text-[var(--muted)] mt-2">
          <span>Used ₹{ltcgUsed.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
          <span>Remaining: ₹{Math.max(0, LTCG_LIMIT - ltcgUsed).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
        </div>
      </div>

      {/* Harvestable Loss Candidates */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-xs sm:text-sm font-semibold text-[var(--text)]">
            Harvestable Loss Candidates
          </h4>
          <span className="text-xs text-[var(--muted)]">
            {candidates.length} {candidates.length === 1 ? 'holding' : 'holdings'} available
          </span>
        </div>

        {candidates.length > 0 ? (
          <div className="overflow-x-auto rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-xs">
            <table className="w-full text-xs sm:text-sm min-w-[500px]">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--muted)] text-[11px] bg-[var(--bg)]">
                  <th className="text-left px-3 sm:px-4 py-2.5 font-medium">Symbol</th>
                  <th className="text-left px-3 sm:px-4 py-2.5 font-medium">Unrealised Loss</th>
                  <th className="text-left px-3 sm:px-4 py-2.5 font-medium">Holding Days</th>
                  <th className="text-left px-3 sm:px-4 py-2.5 font-medium">Tax Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {candidates.map((c, i) => (
                  <tr key={`${c.tradingsymbol}-${i}`} className="hover:bg-[var(--surface-hover)] transition-colors">
                    <td className="px-3 sm:px-4 py-2.5 font-semibold text-[var(--text)]">{c.tradingsymbol}</td>
                    <td className="px-3 sm:px-4 py-2.5 font-medium text-[var(--red)]">
                      -₹{(c.unrealized_loss ?? 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </td>
                    <td className="px-3 sm:px-4 py-2.5 text-[var(--muted)]">{c.holding_period_days} days</td>
                    <td className="px-3 sm:px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[var(--bg)] border border-[var(--border)]">
                        {c.tax_type}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center gap-2 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs sm:text-sm text-emerald-500">
            <CheckCircle2 size={16} className="shrink-0" />
            <span>No tax-loss harvesting candidates needed — portfolio is fully gain-aligned.</span>
          </div>
        )}
      </div>
    </div>
  )
}
