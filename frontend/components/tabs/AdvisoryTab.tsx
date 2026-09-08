'use client'

import { useState } from 'react'
import type { AdvisoryResponse, AdvisoryAction } from '@/lib/types'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface Props { advisory: AdvisoryResponse }

const ACTION_STYLES: Record<AdvisoryAction, string> = {
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

export default function AdvisoryTab({ advisory }: Props) {
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

      {advisory.recommendations?.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium">Recommendations</p>
          {advisory.recommendations.map((r) => <RecCard key={r.symbol} rec={r} />)}
        </div>
      )}

      {!advisory.recommendations?.length && !advisory.rule_flags?.length && (
        <p className="text-sm text-[var(--muted)]">No recommendations available.</p>
      )}
    </div>
  )
}
