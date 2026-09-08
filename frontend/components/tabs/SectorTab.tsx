'use client'

import { useMemo } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, ResponsiveContainer, ReferenceLine, Legend,
} from 'recharts'
import type { Holding } from '@/lib/types'

interface Props { holdings: Holding[]; maxSectorCap: number }

const COLORS = ['#3b82f6','#22c55e','#eab308','#ef4444','#a855f7','#06b6d4','#f97316','#ec4899','#14b8a6','#84cc16']

export default function SectorTab({ holdings, maxSectorCap }: Props) {
  const totalVal = useMemo(() => holdings.reduce((s, h) => s + h.quantity * h.last_price, 0), [holdings])

  const sectorData = useMemo(() => {
    const map: Record<string, number> = {}
    holdings.forEach((h) => { map[h.sector] = (map[h.sector] ?? 0) + h.quantity * h.last_price })
    return Object.entries(map).map(([name, value]) => ({ name, value: parseFloat(value.toFixed(2)) }))
  }, [holdings])

  const capData = useMemo(() => {
    const map: Record<string, number> = {}
    holdings.forEach((h) => { map[h.cap_category] = (map[h.cap_category] ?? 0) + h.quantity * h.last_price })
    return Object.entries(map).map(([name, value]) => ({ name, value: parseFloat(value.toFixed(2)) }))
  }, [holdings])

  const weightData = useMemo(() =>
    holdings
      .map((h) => ({
        name: h.tradingsymbol,
        weight: totalVal > 0 ? parseFloat(((h.quantity * h.last_price / totalVal) * 100).toFixed(2)) : 0,
      }))
      .sort((a, b) => b.weight - a.weight),
    [holdings, totalVal]
  )

  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <p className="text-sm font-medium mb-3">Sector allocation</p>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={sectorData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50} label={(p) => `${p.name ?? ''} ${(((p.percent as number | undefined) ?? 0) * 100).toFixed(0)}%`} labelLine={false}>
                {sectorData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v) => `₹${Number(v).toLocaleString('en-IN')}`} contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div>
          <p className="text-sm font-medium mb-3">Market cap distribution</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={capData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" tick={{ fill: 'var(--muted)', fontSize: 12 }} />
              <YAxis tick={{ fill: 'var(--muted)', fontSize: 12 }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
              <Tooltip formatter={(v) => `₹${Number(v).toLocaleString('en-IN')}`} contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8 }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {capData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div>
        <p className="text-sm font-medium mb-3">Single stock concentration</p>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={weightData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="name" tick={{ fill: 'var(--muted)', fontSize: 11 }} />
            <YAxis tick={{ fill: 'var(--muted)', fontSize: 12 }} unit="%" />
            <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8 }} />
            <ReferenceLine y={maxSectorCap} stroke="var(--red)" strokeDasharray="4 4" label={{ value: `Cap ${maxSectorCap}%`, fill: 'var(--red)', fontSize: 11 }} />
            <Bar dataKey="weight" fill="var(--blue)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
