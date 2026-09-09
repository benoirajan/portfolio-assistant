'use client'

import { useState } from 'react'
import type { AdvisoryResponse, AdvisoryAction, BasketItem } from '@/lib/types'
import { useBasket } from '@/hooks/usePortfolio'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface Props { advisory: AdvisoryResponse }

const ACTION_STYLES: Record<AdvisoryAction | 'TRIM', string> = {
  BUY:  'bg-green-500/10 text-green-400 border-green-500/30',
  HOLD: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  TRIM: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  SELL: 'bg-red-500/10 text-red-400 border-red-500/30',
}

const SEVERITY_COLOR: Record<string, string> = {
  HIGH: 'text-[var(--red)]',
  MEDIUM: 'text-[var(--yellow)]',
  LOW: 'text-[var(--muted)]',
}

function fmt(n: number) {
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

function RecCard({ rec }: { rec: AdvisoryResponse['recommendations'][0] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-[var(--bg)] transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${ACTION_STYLES[rec.action]}`}>
            {rec.action}
          </span>
          <span className="font-medium">{rec.symbol}</span>
          <span className="text-xs text-[var(--muted)]">Target {rec.target_allocation_pct.toFixed(1)}%</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-24 bg-[var(--border)] rounded-full h-1.5">
            <div className="h-1.5 rounded-full bg-[var(--blue)]" style={{ width: `${rec.confidence_score * 100}%` }} />
          </div>
          <span className="text-xs text-[var(--muted)]">{(rec.confidence_score * 100).toFixed(0)}%</span>
          {open ? <ChevronUp size={14} className="text-[var(--muted)]" /> : <ChevronDown size={14} className="text-[var(--muted)]" />}
        </div>
      </button>
      {open && (
        <div className="px-4 pb-3 text-sm text-[var(--muted)] border-t border-[var(--border)] pt-2">
          {rec.rationale}
        </div>
      )}
    </div>
  )
}

function BasketTable({ items, totalBuy, totalSell, budgetPct }: {
  items: BasketItem[]
  totalBuy: number
  totalSell: number
  budgetPct: number
}) {
  return (
    <div className="flex flex-col gap-3">
      <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-[var(--muted)] text-xs">
              <th className="px-4 py-2 text-left">Action</th>
              <th className="px-4 py-2 text-left">Symbol</th>
              <th className="px-4 py-2 text-right">Qty</th>
              <th className="px-4 py-2 text-right">Est. Value</th>
              <th className="px-4 py-2 text-left">Reason</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.symbol} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg)]">
                <td className="px-4 py-2">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${ACTION_STYLES[item.action]}`}>
                    {item.action}
                  </span>
                </td>
                <td className="px-4 py-2 font-medium">{item.symbol}</td>
                <td className="px-4 py-2 text-right">{item.quantity}</td>
                <td className="px-4 py-2 text-right">{fmt(item.estimated_value)}</td>
                <td className="px-4 py-2 text-[var(--muted)] max-w-xs truncate" title={item.reason}>
                  {item.reason}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex gap-4 text-sm flex-wrap">
        <span className="text-green-400">Total buy: {fmt(totalBuy)}</span>
        <span className="text-[var(--red)]">Total sell/trim: {fmt(totalSell)}</span>
        <span className="text-[var(--muted)]">Budget used: {budgetPct.toFixed(1)}%</span>
      </div>
    </div>
  )
}

export default function AdvisoryTab({ advisory }: Props) {
  const [budget, setBudget] = useState('')
  const basket = useBasket()

  const hasRecs = advisory.recommendations?.length > 0
  const budgetNum = parseFloat(budget)
  const canGenerate = hasRecs && !isNaN(budgetNum) && budgetNum > 0

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center gap-2">
        {advisory.source === 'llm' && advisory.llm_provider ? (
          <span className="text-xs bg-green-500/10 text-green-400 border border-green-500/30 px-2 py-1 rounded">
            ✨ {advisory.llm_provider} · {advisory.investment_goal}
          </span>
        ) : (
          <span className="text-xs bg-[var(--surface)] border border-[var(--border)] text-[var(--muted)] px-2 py-1 rounded">
            Rule-based recommendations — set GEMINI_API_KEY to enable AI advisory
          </span>
        )}
      </div>

      {advisory.rule_flags?.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Rule engine alerts</p>
          {advisory.rule_flags.map((f, i) => (
            <div key={i} className="bg-[var(--surface)] border border-[var(--border)] rounded-lg px-4 py-2 flex gap-2 text-sm">
              <span className={`font-medium ${SEVERITY_COLOR[f.severity]}`}>{f.rule}</span>
              <span className="text-[var(--muted)]">— {f.detail}</span>
            </div>
          ))}
        </div>
      )}

      {hasRecs && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Recommendations</p>
          {advisory.recommendations.map((r) => <RecCard key={r.symbol} rec={r} />)}
        </div>
      )}

      {!hasRecs && !advisory.rule_flags?.length && (
        <p className="text-sm text-[var(--muted)]">No recommendations available.</p>
      )}

      {hasRecs && (
        <div className="flex flex-col gap-4 border-t border-[var(--border)] pt-5">
          <p className="text-sm font-medium">Generate trade basket</p>
          <div className="flex gap-3 items-center">
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)] text-sm">₹</span>
              <input
                type="number"
                min={0}
                placeholder="Max budget for buying"
                value={budget}
                onChange={(e) => {
                  setBudget(e.target.value)
                  basket.reset()
                }}
                className="pl-7 pr-4 py-2 bg-[var(--surface)] border border-[var(--border)] rounded-lg text-sm w-56 focus:outline-none focus:border-[var(--blue)]"
              />
            </div>
            <button
              disabled={!canGenerate || basket.isPending}
              onClick={() => basket.mutate({ recommendations: advisory.recommendations, budget: budgetNum })}
              className="px-4 py-2 text-sm rounded-lg bg-[var(--blue)] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
            >
              {basket.isPending ? 'Generating…' : 'Generate Basket'}
            </button>
          </div>

          {basket.isError && (
            <p className="text-sm text-[var(--red)]">Failed to generate basket. Please try again.</p>
          )}

          {basket.isSuccess && basket.data.basket.length === 0 && (
            <p className="text-sm text-[var(--muted)]">No actionable trades — portfolio is already at target allocations within your budget.</p>
          )}

          {basket.isSuccess && basket.data.basket.length > 0 && (
            <BasketTable
              items={basket.data.basket}
              totalBuy={basket.data.total_buy_value}
              totalSell={basket.data.total_sell_value}
              budgetPct={basket.data.budget_utilised_pct}
            />
          )}
        </div>
      )}
    </div>
  )
}
