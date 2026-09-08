'use client'

import { useEffect, useState } from 'react'
import { fetchLoginUrl } from '@/lib/api'
import type { ConnectionMode } from '@/lib/types'
import { Settings, Key, Zap, FlaskConical } from 'lucide-react'

interface Props {
  mode: ConnectionMode
  onModeChange: (m: ConnectionMode) => void
  benchmark: string
  onBenchmarkChange: (v: string) => void
  maxSectorCap: number
  onMaxSectorCapChange: (v: number) => void
  investmentGoal: string
  onInvestmentGoalChange: (v: string) => void
  maxStockCap: number
  onMaxStockCapChange: (v: number) => void
}

const MODES: { id: ConnectionMode; label: string; icon: React.ReactNode }[] = [
  { id: 'demo', label: 'Demo', icon: <FlaskConical size={14} /> },
  { id: 'enctoken', label: 'Enctoken', icon: <Key size={14} /> },
  { id: 'kite', label: 'Kite API', icon: <Zap size={14} /> },
]

const GOALS = ['Moderate Growth', 'Aggressive Growth', 'Capital Preservation', 'Income / Dividend', 'Balanced']

export default function Sidebar({
  mode, onModeChange,
  benchmark, onBenchmarkChange,
  maxSectorCap, onMaxSectorCapChange,
  investmentGoal, onInvestmentGoalChange,
  maxStockCap, onMaxStockCapChange,
}: Props) {
  const [enctoken, setEnctoken] = useState('')
  const [loginUrl, setLoginUrl] = useState('#')

  useEffect(() => {
    const saved = localStorage.getItem('enctoken') ?? ''
    setEnctoken(saved)
  }, [])

  useEffect(() => {
    if (mode === 'kite') fetchLoginUrl().then((r) => setLoginUrl(r.login_url)).catch(() => {})
  }, [mode])

  const saveEnctoken = () => {
    localStorage.setItem('enctoken', enctoken)
    window.location.reload()
  }

  return (
    <aside className="w-64 shrink-0 border-r border-[var(--border)] p-4 flex flex-col gap-5 overflow-y-auto">
      <div>
        <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-2">Connection</p>
        <div className="flex rounded-lg overflow-hidden border border-[var(--border)]">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => onModeChange(m.id)}
              className={`flex-1 flex items-center justify-center gap-1 py-1.5 text-xs transition-colors ${
                mode === m.id
                  ? 'bg-[var(--blue)] text-white'
                  : 'text-[var(--muted)] hover:text-[var(--text)]'
              }`}
            >
              {m.icon}{m.label}
            </button>
          ))}
        </div>

        {mode === 'demo' && (
          <p className="mt-2 text-xs text-[var(--green)]">Using demo portfolio data</p>
        )}

        {mode === 'enctoken' && (
          <div className="mt-2 flex flex-col gap-2">
            <input
              type="password"
              placeholder="Paste enctoken cookie…"
              value={enctoken}
              onChange={(e) => setEnctoken(e.target.value)}
              className="w-full bg-[var(--surface)] border border-[var(--border)] rounded px-2 py-1.5 text-xs outline-none focus:border-[var(--blue)]"
            />
            <button
              onClick={saveEnctoken}
              className="bg-[var(--blue)] text-white text-xs rounded py-1.5 hover:opacity-90 transition-opacity"
            >
              Save & Reload
            </button>
          </div>
        )}

        {mode === 'kite' && (
          <a
            href={loginUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-2 flex items-center justify-center gap-1 bg-[var(--blue)] text-white text-xs rounded py-1.5 hover:opacity-90 transition-opacity"
          >
            <Zap size={12} /> Login with Zerodha
          </a>
        )}
      </div>

      <div>
        <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-2 flex items-center gap-1">
          <Settings size={12} /> Risk & Benchmark
        </p>
        <label className="text-xs text-[var(--muted)]">Benchmark</label>
        <select
          value={benchmark}
          onChange={(e) => onBenchmarkChange(e.target.value)}
          className="mt-1 w-full bg-[var(--surface)] border border-[var(--border)] rounded px-2 py-1.5 text-xs outline-none"
        >
          {['NIFTY 50', 'NIFTY 500', 'SENSEX'].map((b) => <option key={b}>{b}</option>)}
        </select>

        <label className="text-xs text-[var(--muted)] mt-3 block">
          Max sector cap: <span className="text-[var(--text)]">{maxSectorCap}%</span>
        </label>
        <input
          type="range" min={10} max={40} value={maxSectorCap}
          onChange={(e) => onMaxSectorCapChange(Number(e.target.value))}
          className="w-full mt-1 accent-[var(--blue)]"
        />
      </div>

      <div>
        <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-2">AI Advisory</p>
        <label className="text-xs text-[var(--muted)]">Investment goal</label>
        <select
          value={investmentGoal}
          onChange={(e) => onInvestmentGoalChange(e.target.value)}
          className="mt-1 w-full bg-[var(--surface)] border border-[var(--border)] rounded px-2 py-1.5 text-xs outline-none"
        >
          {GOALS.map((g) => <option key={g}>{g}</option>)}
        </select>

        <label className="text-xs text-[var(--muted)] mt-3 block">
          Max single stock: <span className="text-[var(--text)]">{maxStockCap}%</span>
        </label>
        <input
          type="range" min={5} max={40} value={maxStockCap}
          onChange={(e) => onMaxStockCapChange(Number(e.target.value))}
          className="w-full mt-1 accent-[var(--blue)]"
        />
      </div>
    </aside>
  )
}
