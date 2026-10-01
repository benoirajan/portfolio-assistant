'use client'

import { useState, useMemo } from 'react'
import type { ConnectionMode } from '@/lib/types'
import { useHoldings, usePerformance, useTax, useAdvisory } from '@/hooks/usePortfolio'
import { useAuth } from '@/lib/auth-context'
import Header from '@/components/layout/Header'
import Sidebar from '@/components/layout/Sidebar'
import KpiBar from '@/components/kpi/KpiBar'
import HoldingsTab from '@/components/tabs/HoldingsTab'
import SectorTab from '@/components/tabs/SectorTab'
import PerformanceTab from '@/components/tabs/PerformanceTab'
import TaxTab from '@/components/tabs/TaxTab'
import AdvisoryTab from '@/components/tabs/AdvisoryTab'
import { LogIn, Lock } from 'lucide-react'

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
  const [mode, setMode] = useState<ConnectionMode>('enctoken')
  const [benchmark, setBenchmark] = useState('NIFTY 50')
  const [maxSectorCap, setMaxSectorCap] = useState(25)
  const [investmentGoal, setInvestmentGoal] = useState('Moderate Growth')
  const [maxStockCap, setMaxStockCap] = useState(15)

  const { isAuthenticated, openAuthModal } = useAuth()

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
    <div className="flex flex-col h-screen overflow-hidden bg-[var(--bg)] text-[var(--text)]">
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
          {!isAuthenticated ? (
            <div className="m-6 p-6 bg-[var(--surface)] border border-[var(--border)] rounded-2xl flex flex-col items-center justify-center text-center gap-4 my-auto max-w-lg mx-auto shadow-sm">
              <div className="w-14 h-14 rounded-2xl bg-[var(--blue)]/10 text-[var(--blue)] flex items-center justify-center">
                <Lock size={28} />
              </div>
              <div>
                <h3 className="text-lg font-bold tracking-tight">Authentication Required</h3>
                <p className="text-xs text-[var(--muted)] mt-1.5 max-w-sm">
                  Sign in with Google IAM or your email to access your private, tenant-isolated portfolio data and AI advisory.
                </p>
              </div>
              <button
                onClick={openAuthModal}
                className="flex items-center gap-2 px-5 py-2.5 bg-[var(--blue)] text-white font-semibold rounded-xl text-xs hover:opacity-90 transition-all shadow-sm cursor-pointer"
              >
                <LogIn size={15} />
                <span>Sign In or Register</span>
              </button>
            </div>
          ) : (
            <>
              <KpiBar summary={summary} metrics={metrics} />

              <div className="flex border-b border-[var(--border)] px-6 bg-[var(--surface)]">
                {TABS.map((t, i) => (
                  <button
                    key={t}
                    onClick={() => setTab(i)}
                    className={`px-4 py-2.5 text-sm transition-colors border-b-2 -mb-px font-medium cursor-pointer ${
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
                  <div className="flex items-center justify-center h-40 text-[var(--muted)] text-sm">
                    Loading portfolio holdings…
                  </div>
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
            </>
          )}
        </main>
      </div>
    </div>
  )
}
