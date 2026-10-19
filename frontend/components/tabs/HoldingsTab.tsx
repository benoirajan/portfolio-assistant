'use client'

import { useState, useMemo } from 'react'
import type { Holding } from '@/lib/types'
import UploadSection from './UploadSection'
import { UploadCloud, ChevronDown, ChevronUp } from 'lucide-react'

interface Props { holdings: Holding[] }

const fmt = (n?: number) => n != null ? n.toFixed(2) : '—'

export default function HoldingsTab({ holdings }: Props) {
  const [search, setSearch] = useState('')
  const [sectors, setSectors] = useState<string[]>([])
  const [showUpload, setShowUpload] = useState(false)

  const allSectors = useMemo(() => [...new Set(holdings.map((h) => h.sector))].sort(), [holdings])

  const rows = useMemo(() => {
    const totalVal = holdings.reduce((s, h) => s + h.quantity * h.last_price, 0)
    return holdings
      .map((h) => ({
        ...h,
        invested_value: h.quantity * h.average_price,
        current_value: h.quantity * h.last_price,
        pnl: h.quantity * h.last_price - h.quantity * h.average_price,
        pnl_percentage: h.average_price > 0
          ? ((h.last_price - h.average_price) / h.average_price) * 100 : 0,
        weight_pct: totalVal > 0 ? (h.quantity * h.last_price / totalVal) * 100 : 0,
      }))
      .filter((h) =>
        (!search || h.tradingsymbol.toUpperCase().includes(search.toUpperCase())) &&
        (!sectors.length || sectors.includes(h.sector))
      )
  }, [holdings, search, sectors])

  const toggleSector = (s: string) =>
    setSectors((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s])

  if (holdings.length === 0) {
    return (
      <div className="flex flex-col gap-6 max-w-2xl mx-auto py-6">
        <div className="text-center space-y-1">
          <h3 className="text-base font-semibold text-[var(--text)]">No Holdings Found</h3>
          <p className="text-xs text-[var(--muted)]">
            Upload your stock holdings from a Zerodha export or custom CSV/Excel spreadsheet to get started.
          </p>
        </div>
        <UploadSection />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <input
            placeholder="Search symbol…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-[var(--surface)] border border-[var(--border)] rounded px-3 py-1.5 text-sm outline-none focus:border-[var(--blue)] w-48"
          />
          <div className="flex flex-wrap gap-1">
            {allSectors.map((s) => (
              <button
                key={s}
                onClick={() => toggleSector(s)}
                className={`text-xs px-2 py-1 rounded border transition-colors ${
                  sectors.includes(s)
                    ? 'bg-[var(--blue)] border-[var(--blue)] text-white'
                    : 'border-[var(--border)] text-[var(--muted)] hover:text-[var(--text)]'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={() => setShowUpload((prev) => !prev)}
          className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
            showUpload
              ? 'bg-[var(--surface-hover)] border-[var(--blue)] text-[var(--blue)]'
              : 'bg-[var(--surface)] border-[var(--border)] text-[var(--text)] hover:border-[var(--blue)]/60'
          }`}
        >
          <UploadCloud size={14} className="text-[var(--blue)]" />
          <span>Import CSV/Excel</span>
          {showUpload ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {showUpload && (
        <div className="animate-fadeIn">
          <UploadSection
            isCollapsible
            onClose={() => setShowUpload(false)}
            onUploadSuccess={() => setShowUpload(false)}
          />
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-[var(--muted)] text-xs">
              {['Symbol', 'Sector', 'Category', 'Qty', 'Avg Price', 'LTP', 'P&L (₹)', 'P&L (%)', 'Weight', 'P/E', 'P/B', 'ROE', '200 SMA'].map((h) => (
                <th key={h} className="text-left px-3 py-2 whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => {
              const pos = h.pnl >= 0
              return (
                <tr key={h.tradingsymbol} className="border-b border-[var(--border)] hover:bg-[var(--surface)] transition-colors">
                  <td className="px-3 py-2 font-medium">{h.tradingsymbol}</td>
                  <td className="px-3 py-2 text-[var(--muted)] whitespace-nowrap">{h.sector}</td>
                  <td className="px-3 py-2 text-[var(--muted)]">{h.cap_category}</td>
                  <td className="px-3 py-2">{h.quantity}</td>
                  <td className="px-3 py-2">₹{fmt(h.average_price)}</td>
                  <td className="px-3 py-2">₹{fmt(h.last_price)}</td>
                  <td className={`px-3 py-2 font-medium ${pos ? 'text-[var(--green)]' : 'text-[var(--red)]'}`}>
                    ₹{fmt(h.pnl)}
                  </td>
                  <td className={`px-3 py-2 ${pos ? 'text-[var(--green)]' : 'text-[var(--red)]'}`}>
                    {fmt(h.pnl_percentage)}%
                  </td>
                  <td className="px-3 py-2 text-[var(--muted)]">{fmt(h.weight_pct)}%</td>
                  <td className="px-3 py-2 text-[var(--muted)]">{fmt(h.pe_ratio)}</td>
                  <td className="px-3 py-2 text-[var(--muted)]">{fmt(h.pb_ratio)}</td>
                  <td className="px-3 py-2 text-[var(--muted)]">{h.roe != null ? `${fmt(h.roe)}%` : '—'}</td>
                  <td className="px-3 py-2 text-[var(--muted)]">{h.trend_200_sma ?? '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
