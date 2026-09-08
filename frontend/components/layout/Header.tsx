'use client'

import { useEffect, useState } from 'react'
import { checkHealth } from '@/lib/api'
import { TrendingUp, Wifi, WifiOff } from 'lucide-react'

export default function Header() {
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    checkHealth().then(setOnline)
  }, [])

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
      <div className="flex items-center gap-2">
        <TrendingUp className="text-[var(--blue)]" size={22} />
        <span className="font-semibold text-lg tracking-tight">Portfolio Assistant</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        {online === null ? (
          <span className="text-[var(--muted)]">Checking backend…</span>
        ) : online ? (
          <>
            <Wifi size={15} className="text-[var(--green)]" />
            <span className="text-[var(--green)]">Backend online</span>
          </>
        ) : (
          <>
            <WifiOff size={15} className="text-[var(--red)]" />
            <span className="text-[var(--red)]">Backend offline — run uvicorn</span>
          </>
        )}
      </div>
    </header>
  )
}
