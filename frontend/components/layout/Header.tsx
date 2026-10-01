'use client'

import { useEffect, useState } from 'react'
import { checkHealth } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { TrendingUp, Wifi, WifiOff, LogIn, LogOut, User as UserIcon, Shield } from 'lucide-react'

export default function Header() {
  const [online, setOnline] = useState<boolean | null>(null)
  const { user, isAuthenticated, openAuthModal, logout } = useAuth()

  useEffect(() => {
    checkHealth().then(setOnline)
  }, [])

  return (
    <header className="flex items-center justify-between px-6 py-3.5 border-b border-[var(--border)] bg-[var(--surface)]">
      {/* Brand Logo */}
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-[var(--blue)]/10 text-[var(--blue)] flex items-center justify-center">
          <TrendingUp size={18} />
        </div>
        <div>
          <span className="font-bold text-base tracking-tight block">Portfolio Assistant</span>
          <span className="text-[10px] text-[var(--muted)] -mt-1 block">Multi-Tenant AI Advisory</span>
        </div>
      </div>

      {/* Right Side: Backend Status & User Identity */}
      <div className="flex items-center gap-4">
        {/* Backend health pill */}
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-[var(--muted)] px-2.5 py-1 rounded-full bg-[var(--bg)] border border-[var(--border)]">
          {online === null ? (
            <span>Connecting…</span>
          ) : online ? (
            <>
              <Wifi size={13} className="text-[var(--green)]" />
              <span className="text-[var(--green)] font-medium">Online</span>
            </>
          ) : (
            <>
              <WifiOff size={13} className="text-[var(--red)]" />
              <span className="text-[var(--red)] font-medium">Offline</span>
            </>
          )}
        </div>

        {/* User Identity Pill / Login Trigger */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--bg)] border border-[var(--border)]">
              <div className="w-6 h-6 rounded-full bg-[var(--blue)] text-white text-[10px] font-bold flex items-center justify-center uppercase">
                {user.full_name ? user.full_name[0] : user.email[0]}
              </div>
              <div className="flex flex-col text-left">
                <span className="text-xs font-medium text-[var(--text)] max-w-[140px] truncate">
                  {user.full_name || user.email}
                </span>
                <div className="flex items-center gap-1">
                  <span className="text-[9px] font-semibold text-[var(--blue)] uppercase tracking-wider">
                    {user.tier} Tier
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              className="flex items-center gap-1 text-xs text-[var(--muted)] hover:text-red-400 p-2 rounded-lg hover:bg-[var(--surface-hover)] transition-colors cursor-pointer"
            >
              <LogOut size={15} />
              <span className="hidden md:inline">Sign Out</span>
            </button>
          </div>
        ) : (
          <button
            onClick={openAuthModal}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[var(--blue)] text-white text-xs font-semibold rounded-xl hover:opacity-90 transition-all shadow-sm cursor-pointer"
          >
            <LogIn size={14} />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  )
}
