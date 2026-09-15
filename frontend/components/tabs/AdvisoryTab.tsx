'use client'

import { useState, useEffect } from 'react'
import type {
  AdvisoryResponse,
  MultiStagePipelineResponse,
  Stage1Diagnosis,
  Stage2Ranking,
  Stage3Execution,
  BasketItem,
} from '@/lib/types'
import { useZerodhaBaskets, useExportZerodhaBasket } from '@/hooks/usePortfolio'
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  CheckCircle2,
  Sparkles,
  Search,
  ShieldAlert,
  Layers,
  PieChart,
  DollarSign,
  ArrowRight,
  TrendingUp,
  Clock,
  Check,
  AlertCircle,
  Loader2,
} from 'lucide-react'

interface Props {
  advisory: AdvisoryResponse
}

function fmt(n: number) {
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

const TIER_BADGES: Record<string, { label: string; color: string }> = {
  HIGH_CONVICTION: { label: '🟢 High Conviction', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
  GOOD_OPPORTUNITY: { label: '🟢 Good Opportunity', color: 'bg-green-500/10 text-green-400 border-green-500/30' },
  WATCHLIST: { label: '🟡 Watchlist', color: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30' },
  AVOID_FOR_NOW: { label: '🔴 Avoid For Now', color: 'bg-red-500/10 text-red-400 border-red-500/30' },
}

export default function AdvisoryTab({ advisory }: Props) {
  // Form inputs
  const [totalBudget, setTotalBudget] = useState('5000')
  const [monthlyCapacity, setMonthlyCapacity] = useState('10000')
  const [investmentSchedule, setInvestmentSchedule] = useState('Bi-weekly ₹5,000')
  const [investmentGoal, setInvestmentGoal] = useState('Moderate Growth')
  const [allowNewStocks, setAllowNewStocks] = useState(true)

  // SSE Stream / Multi-stage state
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamStage, setStreamStage] = useState<number>(0)
  const [streamMessage, setStreamMessage] = useState<string>('')
  const [pipelineResult, setPipelineResult] = useState<MultiStagePipelineResponse | null>(null)
  const [activeStageTab, setActiveStageTab] = useState<'stage1' | 'stage2' | 'stage3'>('stage3')

  const handleRunPipeline = () => {
    setIsStreaming(true)
    setStreamStage(1)
    setStreamMessage('🔍 Initializing 3-Stage AI Advisory Pipeline...')
    setPipelineResult(null)

    const budgetNum = parseFloat(totalBudget) || 5000
    const capNum = parseFloat(monthlyCapacity) || 10000
    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8000'

    const queryParams = new URLSearchParams({
      total_budget: budgetNum.toString(),
      monthly_capacity: capNum.toString(),
      investment_schedule: investmentSchedule,
      investment_goal: investmentGoal,
      allow_new_stocks: allowNewStocks.toString(),
    })

    const token = typeof window !== 'undefined' ? localStorage.getItem('enctoken') : null
    const url = `${baseUrl}/api/v1/advisory/stream?${queryParams.toString()}`

    const es = new EventSource(url)

    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)
        if (parsed.stage) setStreamStage(parsed.stage)
        if (parsed.message) setStreamMessage(parsed.message)

        if (parsed.status === 'complete' && parsed.full_result) {
          setPipelineResult(parsed.full_result)
          setIsStreaming(false)
          setStreamStage(3)
          setStreamMessage('✅ 3-Stage Advisory Pipeline execution complete!')
          es.close()
        }
      } catch (err) {
        console.error('Failed to parse SSE event:', err)
      }
    }

    es.onerror = (err) => {
      console.error('SSE Error:', err)
      setIsStreaming(false)
      es.close()
    }
  }

  const s1 = pipelineResult?.stage1
  const s2 = pipelineResult?.stage2
  const s3 = pipelineResult?.stage3

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header Card */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="text-amber-400" size={20} />
            <h3 className="text-lg font-bold">3-Stage Interactive AI Advisor</h3>
          </div>
          <p className="text-xs text-[var(--muted)] mt-1">
            Deep multi-pass reasoning pipeline (`prompt1.md` Diagnosis ➔ `Prompt2.md` Conviction ➔ `prompt3.md` Bounded Decision)
          </p>
        </div>
        <div className="flex items-center gap-2">
          {pipelineResult ? (
            <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-full font-medium flex items-center gap-1.5">
              <CheckCircle2 size={14} /> Synced via {pipelineResult.llm_provider || 'Gemini 3.6 Flash'}
            </span>
          ) : (
            <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded-full font-medium">
              Ready for 3-Stage Reasoning
            </span>
          )}
        </div>
      </div>

      {/* Input Parameters Form */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col gap-4">
        <h4 className="text-sm font-semibold text-[var(--muted)] uppercase tracking-wider">Investment Cycle Parameters</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 text-sm">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--muted)]">Today's Budget (₹)</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]">₹</span>
              <input
                type="number"
                min={0}
                value={totalBudget}
                onChange={(e) => setTotalBudget(e.target.value)}
                className="pl-7 pr-3 py-2 bg-[var(--bg)] border border-[var(--border)] rounded-lg w-full focus:outline-none focus:border-[var(--blue)] font-medium"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--muted)]">Monthly Capacity (₹)</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]">₹</span>
              <input
                type="number"
                min={0}
                value={monthlyCapacity}
                onChange={(e) => setMonthlyCapacity(e.target.value)}
                className="pl-7 pr-3 py-2 bg-[var(--bg)] border border-[var(--border)] rounded-lg w-full focus:outline-none focus:border-[var(--blue)]"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--muted)]">Schedule Frequency</label>
            <select
              value={investmentSchedule}
              onChange={(e) => setInvestmentSchedule(e.target.value)}
              className="px-3 py-2 bg-[var(--bg)] border border-[var(--border)] rounded-lg w-full focus:outline-none focus:border-[var(--blue)]"
            >
              <option value="Bi-weekly ₹5,000">Bi-weekly (₹5,000 / 2 weeks)</option>
              <option value="Monthly Lump-sum ₹10,000">Monthly Lump-sum (₹10,000 / mo)</option>
              <option value="Weekly SIP">Weekly SIP</option>
              <option value="Custom">Custom Schedule</option>
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--muted)]">Risk & Goal Strategy</label>
            <select
              value={investmentGoal}
              onChange={(e) => setInvestmentGoal(e.target.value)}
              className="px-3 py-2 bg-[var(--bg)] border border-[var(--border)] rounded-lg w-full focus:outline-none focus:border-[var(--blue)]"
            >
              <option value="Moderate Growth">Moderate Growth (10+ yrs)</option>
              <option value="Aggressive Growth">Aggressive Growth</option>
              <option value="Capital Preservation">Capital Preservation</option>
              <option value="Balanced">Balanced</option>
            </select>
          </div>

          <div className="flex flex-col gap-1 justify-end">
            <label className="flex items-center gap-2 cursor-pointer pb-2 text-xs">
              <input
                type="checkbox"
                checked={allowNewStocks}
                onChange={(e) => setAllowNewStocks(e.target.checked)}
                className="accent-[var(--blue)] rounded"
              />
              Screen New Stock Ideas
            </label>
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t border-[var(--border)]">
          <button
            disabled={isStreaming}
            onClick={handleRunPipeline}
            className="px-5 py-2.5 rounded-lg bg-[var(--blue)] text-white font-medium hover:opacity-90 disabled:opacity-50 transition-opacity flex items-center gap-2 shadow-lg shadow-blue-500/10 text-sm"
          >
            {isStreaming ? (
              <>
                <Loader2 className="animate-spin" size={16} /> Running Pipeline…
              </>
            ) : (
              <>
                <Sparkles size={16} /> Run 3-Stage AI Advisory
              </>
            )}
          </button>
        </div>
      </div>

      {/* Live SSE Streaming Progress Banner */}
      {isStreaming && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-blue-400 font-medium text-sm">
              <Loader2 className="animate-spin text-blue-400" size={18} />
              <span>{streamMessage}</span>
            </div>
            <span className="text-xs bg-blue-500/20 text-blue-300 px-2.5 py-1 rounded-full font-mono">
              Stage {streamStage} of 3
            </span>
          </div>

          {/* Stepper Progress Bar */}
          <div className="grid grid-cols-3 gap-2">
            <div className={`h-1.5 rounded-full transition-all duration-500 ${streamStage >= 1 ? 'bg-blue-500' : 'bg-[var(--border)]'}`} />
            <div className={`h-1.5 rounded-full transition-all duration-500 ${streamStage >= 2 ? 'bg-blue-500' : 'bg-[var(--border)]'}`} />
            <div className={`h-1.5 rounded-full transition-all duration-500 ${streamStage >= 3 ? 'bg-blue-500' : 'bg-[var(--border)]'}`} />
          </div>
        </div>
      )}

      {/* Results Section (Rendered when pipeline finishes or fallback loaded) */}
      {pipelineResult && (
        <div className="flex flex-col gap-5">
          {/* Stage Tabs */}
          <div className="flex gap-2 border-b border-[var(--border)] pb-2 text-sm">
            <button
              onClick={() => setActiveStageTab('stage3')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeStageTab === 'stage3' ? 'bg-[var(--surface)] text-white border border-[var(--border)]' : 'text-[var(--muted)] hover:text-white'
              }`}
            >
              Stage 3: Execution Plan & Basket
            </button>
            <button
              onClick={() => setActiveStageTab('stage2')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeStageTab === 'stage2' ? 'bg-[var(--surface)] text-white border border-[var(--border)]' : 'text-[var(--muted)] hover:text-white'
              }`}
            >
              Stage 2: Opportunity Conviction Matrix
            </button>
            <button
              onClick={() => setActiveStageTab('stage1')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeStageTab === 'stage1' ? 'bg-[var(--surface)] text-white border border-[var(--border)]' : 'text-[var(--muted)] hover:text-white'
              }`}
            >
              Stage 1: Portfolio Health Audit
            </button>
          </div>

          {/* STAGE 3 VIEW */}
          {activeStageTab === 'stage3' && s3 && (
            <div className="flex flex-col gap-6">
              {/* Primary Decision Banner */}
              <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs uppercase font-bold text-[var(--muted)] tracking-wider">Final Decision</span>
                    <span
                      className={`text-xs font-extrabold px-3 py-1 rounded-full border ${
                        s3.action === 'BUY'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : s3.action === 'PARTIALLY_INVEST'
                          ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
                          : 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                      }`}
                    >
                      {s3.action}
                    </span>
                  </div>
                  <h4 className="text-base font-semibold mt-2">{s3.simple_action_recommendation}</h4>
                </div>
                <div className="flex gap-4 text-sm bg-[var(--bg)] p-3 rounded-lg border border-[var(--border)]">
                  <div>
                    <span className="text-xs text-[var(--muted)] block">Total Allocated</span>
                    <span className="font-bold text-emerald-400">{fmt(s3.allocated_amount)}</span>
                  </div>
                  <div className="border-l border-[var(--border)] pl-4">
                    <span className="text-xs text-[var(--muted)] block">Cash Buffer</span>
                    <span className="font-bold text-[var(--muted)]">{fmt(s3.cash_to_keep)}</span>
                  </div>
                </div>
              </div>

              {/* Purchases Table */}
              {s3.purchases?.length > 0 ? (
                <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col gap-3">
                  <h4 className="font-semibold text-sm">Calculated Whole-Share Basket</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-[var(--border)] text-[var(--muted)] text-xs">
                          <th className="px-4 py-2 text-left">Action</th>
                          <th className="px-4 py-2 text-left">Symbol</th>
                          <th className="px-4 py-2 text-right">LTP Price</th>
                          <th className="px-4 py-2 text-right">Qty</th>
                          <th className="px-4 py-2 text-right">Total Spend</th>
                          <th className="px-4 py-2 text-left">Rationale</th>
                        </tr>
                      </thead>
                      <tbody>
                        {s3.purchases.map((p) => (
                          <tr key={p.symbol} className="border-b border-[var(--border)] last:border-0 hover:bg-[var(--bg)]">
                            <td className="px-4 py-2.5">
                              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                {p.action}
                              </span>
                            </td>
                            <td className="px-4 py-2.5 font-bold">{p.symbol}</td>
                            <td className="px-4 py-2.5 text-right">{fmt(p.current_price)}</td>
                            <td className="px-4 py-2.5 text-right font-semibold">{p.quantity}</td>
                            <td className="px-4 py-2.5 text-right font-bold text-emerald-400">{fmt(p.amount)}</td>
                            <td className="px-4 py-2.5 text-[var(--muted)] max-w-xs truncate">{p.rationale}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Zerodha Export Component */}
                  <ZerodhaExportSection
                    items={s3.purchases
                      .filter((p) => p.action !== 'HOLD')
                      .map((p) => ({
                        symbol: p.symbol,
                        action: p.action as 'BUY' | 'SELL' | 'TRIM',
                        quantity: p.quantity,
                        estimated_value: p.amount,
                        reason: p.rationale,
                      }))}
                  />
                </div>
              ) : (
                <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 text-sm text-[var(--muted)]">
                  No purchases recommended for this cycle. The AI advisor recommends holding cash in your buffer.
                </div>
              )}

              {/* Rationale Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 flex flex-col gap-2">
                  <h5 className="font-semibold text-xs text-[var(--muted)] uppercase tracking-wider">Why This Decision?</h5>
                  <ul className="text-sm flex flex-col gap-1.5">
                    {s3.why_this_decision?.map((item, i) => (
                      <li key={i} className="flex gap-2 items-start">
                        <span className="text-emerald-400 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 flex flex-col gap-2">
                  <h5 className="font-semibold text-xs text-[var(--muted)] uppercase tracking-wider">Why Not Other Candidates?</h5>
                  <p className="text-sm text-[var(--muted)]">{s3.why_not_others}</p>
                </div>
              </div>
            </div>
          )}

          {/* STAGE 2 VIEW */}
          {activeStageTab === 'stage2' && s2 && (
            <div className="flex flex-col gap-6">
              <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col gap-2">
                <h4 className="font-bold text-base">Opportunity Screening Summary</h4>
                <p className="text-sm">{s2.opportunity_summary}</p>
                <div className="mt-2 p-3 bg-[var(--bg)] rounded-lg border border-[var(--border)] text-xs text-emerald-400">
                  💡 <strong>Recommendation:</strong> {s2.existing_vs_new_recommendation}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {s2.top_opportunities?.map((cand) => {
                  const badge = TIER_BADGES[cand.conviction_tier] || TIER_BADGES['GOOD_OPPORTUNITY']
                  return (
                    <div key={cand.symbol} className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-base">{cand.symbol}</span>
                          <span className="text-xs text-[var(--muted)]">({cand.sector})</span>
                          {cand.is_existing_holding && (
                            <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded">
                              Holding
                            </span>
                          )}
                        </div>
                        <span className={`text-xs px-2.5 py-0.5 rounded-full border ${badge.color}`}>{badge.label}</span>
                      </div>
                      <p className="text-sm">{cand.rationale}</p>
                      <div className="text-xs text-[var(--muted)] border-t border-[var(--border)] pt-2 flex justify-between">
                        <span>Valuation: {cand.valuation_assessment}</span>
                        <span>Main Risk: {cand.main_risk}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* STAGE 1 VIEW */}
          {activeStageTab === 'stage1' && s1 && (
            <div className="flex flex-col gap-6">
              <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col gap-3">
                <h4 className="font-bold text-base">Overall Portfolio Quality Audit</h4>
                <p className="text-sm">{s1.overall_quality}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs mt-2">
                  <div className="bg-[var(--bg)] p-3 rounded-lg border border-[var(--border)]">
                    <strong className="text-emerald-400 block mb-1">Main Strength:</strong>
                    <span>{s1.main_strength}</span>
                  </div>
                  <div className="bg-[var(--bg)] p-3 rounded-lg border border-[var(--border)]">
                    <strong className="text-amber-400 block mb-1">Main Weakness:</strong>
                    <span>{s1.main_weakness}</span>
                  </div>
                </div>
              </div>

              {/* Sector breakdown */}
              <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col gap-3">
                <h4 className="font-semibold text-sm">Sector Allocation Diagnosis</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  {s1.sector_analysis?.map((sec) => (
                    <div key={sec.sector} className="bg-[var(--bg)] border border-[var(--border)] p-3 rounded-lg flex flex-col gap-1">
                      <div className="flex justify-between font-bold">
                        <span>{sec.sector}</span>
                        <span>{sec.weight_pct.toFixed(1)}%</span>
                      </div>
                      <span className="text-[10px] text-[var(--muted)]">{sec.comment}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Fallback Display if no pipeline run yet */}
      {!pipelineResult && !isStreaming && advisory.recommendations?.length > 0 && (
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-5 flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <h4 className="font-bold text-sm">Current Holdings Recommendations</h4>
            <span className="text-xs text-[var(--muted)]">Click "Run 3-Stage AI Advisory" above for deep multi-pass reasoning</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {advisory.recommendations.map((r) => (
              <div key={r.symbol} className="bg-[var(--bg)] border border-[var(--border)] rounded-lg p-3 text-sm flex flex-col gap-1">
                <div className="flex justify-between font-medium">
                  <span>{r.symbol}</span>
                  <span className="text-xs font-bold text-emerald-400">{r.action}</span>
                </div>
                <p className="text-xs text-[var(--muted)]">{r.rationale}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ZerodhaExportSection({ items }: { items: BasketItem[] }) {
  const defaultName = `Portfolio Rebalance ${new Date().toISOString().slice(0, 10)}`
  const [mode, setMode] = useState<'new' | 'existing'>('new')
  const [basketName, setBasketName] = useState(defaultName)
  const [selectedBasketId, setSelectedBasketId] = useState('')

  const { data: zerodhaData, isLoading: loadingBaskets } = useZerodhaBaskets()
  const exportMutation = useExportZerodhaBasket()

  const existingBaskets = zerodhaData?.baskets ?? []

  const handleExport = () => {
    const exportItems = items.map((i) => ({
      symbol: i.symbol,
      action: i.action,
      quantity: i.quantity,
    }))

    const selectedBasket = existingBaskets.find((b) => b.id === selectedBasketId)
    const nameToUse = mode === 'existing' && selectedBasket ? selectedBasket.name : basketName

    exportMutation.mutate({
      basket_name: nameToUse,
      basket_id: mode === 'existing' ? selectedBasketId : undefined,
      items: exportItems,
    })
  }

  return (
    <div className="bg-[var(--surface)] border border-[var(--border)] rounded-lg p-4 flex flex-col gap-4 mt-2">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-sm">Export to Zerodha Baskets</h4>
          <p className="text-xs text-[var(--muted)]">
            Create or append to a Zerodha basket without executing orders. Trades can be manually executed on Zerodha Kite.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-3 text-sm">
        <div className="flex gap-4 items-center">
          <label className="flex items-center gap-2 cursor-pointer text-xs">
            <input
              type="radio"
              name="basketMode"
              checked={mode === 'new'}
              onChange={() => setMode('new')}
              className="accent-[var(--blue)]"
            />
            Create New Basket
          </label>
          <label className="flex items-center gap-2 cursor-pointer text-xs">
            <input
              type="radio"
              name="basketMode"
              checked={mode === 'existing'}
              onChange={() => setMode('existing')}
              className="accent-[var(--blue)]"
            />
            Add to Existing Basket
          </label>
        </div>

        {mode === 'new' ? (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--muted)]">Basket Name</label>
            <input
              type="text"
              value={basketName}
              onChange={(e) => setBasketName(e.target.value)}
              className="px-3 py-1.5 bg-[var(--bg)] border border-[var(--border)] rounded-md text-sm w-72 focus:outline-none focus:border-[var(--blue)]"
              placeholder="e.g. Portfolio Rebalance"
            />
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-[var(--muted)]">Select Zerodha Basket</label>
            {loadingBaskets ? (
              <p className="text-xs text-[var(--muted)]">Loading baskets…</p>
            ) : existingBaskets.length === 0 ? (
              <p className="text-xs text-[var(--muted)]">No existing baskets found. Please create a new basket.</p>
            ) : (
              <select
                value={selectedBasketId}
                onChange={(e) => setSelectedBasketId(e.target.value)}
                className="px-3 py-1.5 bg-[var(--bg)] border border-[var(--border)] rounded-md text-sm w-72 focus:outline-none focus:border-[var(--blue)]"
              >
                <option value="">Select a basket…</option>
                {existingBaskets.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} {b.item_count !== undefined ? `(${b.item_count} items)` : ''}
                  </option>
                ))}
              </select>
            )}
          </div>
        )}

        <div className="flex items-center gap-3 mt-1">
          <button
            disabled={exportMutation.isPending || (mode === 'new' && !basketName.trim()) || (mode === 'existing' && !selectedBasketId)}
            onClick={handleExport}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {exportMutation.isPending ? 'Pushing to Zerodha…' : 'Push to Zerodha Basket'}
          </button>
        </div>

        {exportMutation.isError && (
          <p className="text-xs text-[var(--red)]">
            {(exportMutation.error as Error)?.message || 'Failed to export basket to Zerodha. Check your Zerodha connection.'}
          </p>
        )}

        {exportMutation.isSuccess && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-3 flex flex-col gap-2 text-xs text-emerald-400">
            <div className="flex items-center gap-2 font-medium">
              <CheckCircle2 size={16} />
              <span>{exportMutation.data.message}</span>
            </div>
            <a
              href={exportMutation.data.kite_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 font-semibold underline hover:text-emerald-300 w-fit"
            >
              Open Zerodha Kite Baskets <ExternalLink size={14} />
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
