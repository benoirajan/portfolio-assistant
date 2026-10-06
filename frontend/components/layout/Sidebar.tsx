'use client'

import { useEffect, useState } from 'react'
import { fetchLoginUrl } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import type { ConnectionMode } from '@/lib/types'
import { Settings, Key, Zap, CheckCircle2, AlertTriangle, ShieldCheck, LogIn, Trash2 } from 'lucide-react'

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

function SliderWithInput({
  min, max, value, onChange,
}: { min: number; max: number; value: number; onChange: (v: number) => void }) {
  const [draft, setDraft] = useState(String(value))

  useEffect(() => { setDraft(String(value)) }, [value])

  const commit = (raw: string) => {
    const v = Math.min(max, Math.max(min, Number(raw)))
    if (!isNaN(v) && raw !== '') onChange(v)
    else setDraft(String(value))
  }

  return (
    <div className="flex items-center gap-2 mt-1">
      <input
        type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 accent-[var(--blue)]"
      />
      <input
        type="number" min={min} max={max} value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={(e) => commit(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && commit(draft)}
        className="w-14 bg-[var(--surface)] border border-[var(--border)] rounded px-1.5 py-0.5 text-xs text-center outline-none focus:border-[var(--blue)] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
      />
    </div>
  )
}

const MODES: { id: ConnectionMode; label: string; icon: React.ReactNode }[] = [
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
  const { isAuthenticated, brokerStatus, saveEnctoken, disconnectBrokerSession, openAuthModal } = useAuth()
  const [enctokenInput, setEnctokenInput] = useState('')
  const [loginUrl, setLoginUrl] = useState('#')
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  useEffect(() => {
    if (mode === 'kite') fetchLoginUrl().then((r) => setLoginUrl(r.login_url)).catch(() => {})
  }, [mode])

  const handleSaveEnctoken = async () => {
    if (!enctokenInput.trim()) return
    setIsSaving(true)
    try {
      await saveEnctoken(enctokenInput.trim())
      setSaveSuccess(true)
      setEnctokenInput('')
      setTimeout(() => {
        setSaveSuccess(false)
        window.location.reload()
      }, 1000)
    } catch (e) {
      console.error(e)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <aside className="w-64 shrink-0 border-r border-[var(--border)] p-4 flex flex-col gap-5 overflow-y-auto bg-[var(--surface)]">
      {/* Broker Session & Multi-Tenancy */}
      <div>
        <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-2 flex items-center justify-between">
          <span>Broker Connection</span>
          <ShieldCheck size={13} className="text-[var(--blue)]" />
        </p>

        {!isAuthenticated ? (
          <div className="p-3 bg-[var(--bg)] border border-[var(--border)] rounded-xl flex flex-col gap-2">
            <p className="text-xs text-[var(--muted)]">
              Sign in to sync your private portfolio and encrypt broker credentials.
            </p>
            <button
              onClick={openAuthModal}
              className="w-full flex items-center justify-center gap-1.5 py-2 bg-[var(--blue)] text-white text-xs font-semibold rounded-lg hover:opacity-90 transition-opacity cursor-pointer"
            >
              <LogIn size={13} /> Sign In
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {brokerStatus?.has_enctoken ? (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
                    <CheckCircle2 size={15} />
                    <span>Zerodha Connected</span>
                  </div>
                  <button
                    onClick={disconnectBrokerSession}
                    title="Disconnect Zerodha Session"
                    className="text-red-400 hover:text-red-300 p-1 rounded hover:bg-red-500/10 transition-colors cursor-pointer"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
                <p className="text-[10px] text-[var(--muted)]">
                  Session token encrypted at rest via Fernet AES-256.
                </p>
              </div>
            ) : (
              <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center gap-2 text-xs text-amber-400">
                <AlertTriangle size={15} className="shrink-0" />
                <span>No broker credentials saved yet.</span>
              </div>
            )}

            <div className="flex rounded-lg overflow-hidden border border-[var(--border)]">
              {MODES.map((m) => (
                <button
                  key={m.id}
                  onClick={() => onModeChange(m.id)}
                  className={`flex-1 flex items-center justify-center gap-1 py-1.5 text-xs transition-colors cursor-pointer ${
                    mode === m.id
                      ? 'bg-[var(--blue)] text-white font-medium'
                      : 'text-[var(--muted)] hover:text-[var(--text)]'
                  }`}
                >
                  {m.icon}{m.label}
                </button>
              ))}
            </div>

            {mode === 'enctoken' && (
              <div className="flex flex-col gap-2">
                <input
                  type="password"
                  placeholder="Paste Zerodha enctoken…"
                  value={enctokenInput}
                  onChange={(e) => setEnctokenInput(e.target.value)}
                  className="w-full bg-[var(--bg)] border border-[var(--border)] rounded-lg px-2.5 py-1.5 text-xs outline-none focus:border-[var(--blue)]"
                />
                <button
                  onClick={handleSaveEnctoken}
                  disabled={isSaving || !enctokenInput.trim()}
                  className="bg-[var(--blue)] text-white text-xs font-semibold rounded-lg py-1.5 hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
                >
                  {isSaving ? 'Encrypting & Saving…' : saveSuccess ? 'Saved!' : 'Save & Encrypt'}
                </button>
              </div>
            )}

            {mode === 'kite' && (
              <a
                href={loginUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center gap-1 bg-[var(--blue)] text-white text-xs font-semibold rounded-lg py-1.5 hover:opacity-90 transition-opacity"
              >
                <Zap size={12} /> Login with Zerodha Kite
              </a>
            )}
          </div>
        )}
      </div>

      {/* Risk & Benchmark Controls */}
      <div>
        <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-2 flex items-center gap-1">
          <Settings size={12} /> Risk & Benchmark
        </p>
        <label className="text-xs text-[var(--muted)]">Benchmark</label>
        <select
          value={benchmark}
          onChange={(e) => onBenchmarkChange(e.target.value)}
          className="mt-1 w-full bg-[var(--bg)] border border-[var(--border)] rounded-lg px-2 py-1.5 text-xs outline-none focus:border-[var(--blue)]"
        >
          {['NIFTY 50', 'NIFTY 500', 'SENSEX'].map((b) => <option key={b}>{b}</option>)}
        </select>

        <label className="text-xs text-[var(--muted)] mt-3 block">Max sector cap (%)</label>
        <SliderWithInput min={10} max={60} value={maxSectorCap} onChange={onMaxSectorCapChange} />
      </div>

      {/* AI Advisory Settings */}
      <div>
        <p className="text-xs text-[var(--muted)] uppercase tracking-wider mb-2">AI Advisory</p>
        <label className="text-xs text-[var(--muted)]">Investment goal</label>
        <select
          value={investmentGoal}
          onChange={(e) => onInvestmentGoalChange(e.target.value)}
          className="mt-1 w-full bg-[var(--bg)] border border-[var(--border)] rounded-lg px-2 py-1.5 text-xs outline-none focus:border-[var(--blue)]"
        >
          {GOALS.map((g) => <option key={g}>{g}</option>)}
        </select>

        <label className="text-xs text-[var(--muted)] mt-3 block">Max single stock (%)</label>
        <SliderWithInput min={5} max={50} value={maxStockCap} onChange={onMaxStockCapChange} />
      </div>
    </aside>
  )
}
