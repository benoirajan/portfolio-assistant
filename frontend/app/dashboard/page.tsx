'use client'

import { useState, useMemo } from 'react'
import type { ConnectionMode } from '@/lib/types'
import { useHoldings, usePerformance, useTax, useMargins, useAdvisory } from '@/hooks/usePortfolio'
import Header from '@/components/layout/Header'
import Sidebar from '@/components/layout/Sidebar'
import KpiBar from '@/components/kpi/KpiBar'
import HoldingsTab from '@/components/tabs/HoldingsTab'
import SectorTab from '@/components/tabs/SectorTab'
import PerformanceTab from '@/components/tabs/PerformanceTab'
import TaxTab from '@/components/tabs/TaxTab'
import AdvisoryTab from '@/components/tabs/AdvisoryTab'

const TABS = [
  '📊 Holdings',
  '🍕 Sector',
  '📈 Performance',
  '⚖️ Tax',
  '🤖 Advisory',
]

const EMPTY_SUMMARY = { total_holdings_count: 0, total_investment: 0, current_value: 0, total_pnl: 0, total_pnl_percentage: 0 }
const EMPTY_METRICS = { xirr_percentage: 0, sharpe_ratio: 0, sortino_ratio: 0, portfolio_beta: 1, weighted_pe: 0, weighted_roe: 0, herfindahl_index: 0, risk_profile_tag: '—' }
const EMPTY_TAX = { net_stcg: 0, stcg_tax_payable: 0, net_ltcg: 0, ltcg_tax_payable: 0, ltcg_exemption_used: 0, harvestable_loss_candidates: [] }
const EMPTY_ADVISORY = { status: '', source: 'rule_engine' as const, investment_goal: '', rule_flags: [], recommendations: [] }

export default function Dashboard() {
  const [tab, setTab] = useState(0)
  const [mode, setMode] = useState<ConnectionMode>('demo')
  const [benchmark, setBenchmark] = useState('NIFTY 50')
  const [maxSectorCap, setMaxSectorCap] = useState(25)
  const [investmentGoal, setInvestmentGoal] = useState('Moderate Growth')
  const [maxStockCap, setMaxStockCap] = useState(15)

  const { data: holdingsData, isLoading: hLoading } = useHoldings()
  const { data: perfData } = usePerformance()
  const { data: taxData } = useTax()
  const { data: advisoryData } = useAdvisory(investmentGoal, maxStockCap, maxSectorCap)

  const holdings = useMemo(() => holdingsData?.holdings ?? [], [holdingsData])
  const summary = holdingsData?.summary ?? EMPTY_SUMMARY
  const metrics = perfData?.metrics ?? EMPTY_METRICS
  const tax = taxData?.tax_analysis ?? EMPTY_TAX
  const advisory = advisoryData ?? EMPTY_ADVISORY

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          mode={mode} onModeChange={setMode}
          benchmark={benchmark} onBenchmarkChange={setBenchmark}
          maxSectorCap={maxSectorCap} onMaxSectorCapChange={setMaxSectorCap}
          investmentGoal={investmentGoal} onInvestmentGoalChange={setInvestmentGoal}
          maxStockCap={maxStockCap} onMaxStockCapChange={setMaxStockCap}
        />
        <main className="flex-1 flex flex-col overflow-hidden">
          <KpiBar summary={summary} metrics={metrics} />

          <div className="flex border-b border-[var(--border)] px-6">
            {TABS.map((t, i) => (
              <button
                key={t}
                onClick={() => setTab(i)}
                className={`px-4 py-2.5 text-sm transition-colors border-b-2 -mb-px ${
                  tab === i
                    ? 'border-[var(--blue)] text-[var(--text)]'
                    : 'border-transparent text-[var(--muted)] hover:text-[var(--text)]'
                }`}
              >
                {t}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {hLoading ? (
              <div className="flex items-center justify-center h-40 text-[var(--muted)]">Loading…</div>
            ) : (
              <>
                {tab === 0 && <HoldingsTab holdings={holdings} />}
                {tab === 1 && <SectorTab holdings={holdings} maxSectorCap={maxSectorCap} />}
                {tab === 2 && <PerformanceTab metrics={metrics} />}
                {tab === 3 && <TaxTab tax={tax} />}
                {tab === 4 && <AdvisoryTab advisory={advisory} />}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
