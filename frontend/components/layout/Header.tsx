'use client'

import { useEffect, useState, useCallback } from 'react'
import { checkHealth, fetchAiQuota } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import {
  TrendingUp,
  Wifi,
  WifiOff,
  LogIn,
  LogOut,
  Sparkles,
  ArrowUpCircle,
  Menu,
  PanelLeft,
} from 'lucide-react'
import type { AiQuotaResponse } from '@/lib/types'
import PricingModal from '@/components/billing/PricingModal'
import ThemeToggle from './ThemeToggle'

interface HeaderProps {
  onToggleSidebar?: () => void
  onToggleMobileMenu?: () => void
  isSidebarOpen?: boolean
}

export default function Header({ onToggleSidebar, onToggleMobileMenu, isSidebarOpen = true }: HeaderProps) {
  const [online, setOnline] = useState<boolean | null>(null)
  const [quota, setQuota] = useState<AiQuotaResponse | null>(null)
  const [isPricingOpen, setIsPricingOpen] = useState(false)
  const { user, isAuthenticated, openAuthModal, logout, refreshUser } = useAuth()

  useEffect(() => {
    checkHealth().then(setOnline)
  }, [])

  const loadQuota = useCallback(async () => {
    if (!isAuthenticated) return
    try {
      const q = await fetchAiQuota()
      setQuota(q)
    } catch {
      // quota pill is non-critical — silently fail
    }
  }, [isAuthenticated])

  useEffect(() => {
    loadQuota()
  }, [loadQuota, user?.tier])

  const handleUpgradeSuccess = useCallback(
    async (_newTier: string) => {
      await refreshUser()
      await loadQuota()
    },
    [refreshUser, loadQuota]
  )

  const currentTier = (user?.tier ?? 'FREE').toUpperCase()
  const showUpgradeBtn = isAuthenticated && currentTier !== 'ELITE'

  return (
    <>
      <header className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-3.5 border-b border-[var(--border)] bg-[var(--surface)] z-30">
        {/* Brand & Sidebar Toggles */}
        <div className="flex items-center gap-2 sm:gap-3">
          {isAuthenticated && (
            <>
              {/* Mobile Drawer Trigger (md:hidden) */}
              <button
                onClick={onToggleMobileMenu || onToggleSidebar}
                className="md:hidden p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors cursor-pointer"
                aria-label="Open sidebar drawer"
                title="Open controls"
              >
                <Menu size={20} />
              </button>

              {/* Desktop Collapsible Toggle (hidden md:flex) */}
              {onToggleSidebar && (
                <button
                  onClick={onToggleSidebar}
                  className={`hidden md:flex p-1.5 rounded-lg transition-colors cursor-pointer ${
                    isSidebarOpen
                      ? 'text-[var(--blue)] hover:bg-[var(--blue)]/10'
                      : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)]'
                  }`}
                  aria-label={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
                  title={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
                >
                  <PanelLeft size={18} />
                </button>
              )}
            </>
          )}

          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[var(--blue)]/10 text-[var(--blue)] flex items-center justify-center shrink-0">
              <TrendingUp size={18} />
            </div>
            <div>
              <span className="font-bold text-sm sm:text-base tracking-tight block">Portfolio Assistant</span>
              <span className="text-[9px] sm:text-[10px] text-[var(--muted)] -mt-1 block">Multi-Tenant AI Advisory</span>
            </div>
          </div>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-2 sm:gap-3">
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

          {/* Theme switcher */}
          <ThemeToggle />

          {isAuthenticated && user ? (
            <div className="flex items-center gap-1.5 sm:gap-2">
              {/* AI Quota pill (only shown when quota data is available) */}
              {quota && (
                <div
                  title={`${quota.used} of ${quota.limit === 9999 ? '∞' : quota.limit} AI runs used this month`}
                  className="hidden md:flex items-center gap-1 px-2.5 py-1 rounded-full bg-[var(--bg)] border border-[var(--border)] text-[10px] text-[var(--muted)] cursor-default select-none"
                >
                  <Sparkles size={11} className="text-amber-500 dark:text-amber-400" />
                  <span>
                    {quota.used}/{quota.limit === 9999 ? '∞' : quota.limit} AI
                  </span>
                </div>
              )}

              {/* Upgrade button — hidden for ELITE users */}
              {showUpgradeBtn && (
                <button
                  onClick={() => setIsPricingOpen(true)}
                  className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/40 rounded-full hover:bg-amber-500/10 transition-colors cursor-pointer"
                >
                  <ArrowUpCircle size={12} />
                  <span className="hidden sm:inline">Upgrade</span>
                </button>
              )}

              {/* User identity pill */}
              <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-xl bg-[var(--bg)] border border-[var(--border)]">
                <div className="w-6 h-6 rounded-full bg-[var(--blue)] text-white text-[10px] font-bold flex items-center justify-center uppercase shrink-0">
                  {user.full_name ? user.full_name[0] : user.email[0]}
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-medium text-[var(--text)] max-w-[80px] sm:max-w-[130px] truncate">
                    {user.full_name || user.email}
                  </span>
                  <div className="flex items-center gap-1">
                    <span
                      className={`text-[9px] font-semibold uppercase tracking-wider ${
                        currentTier === 'ELITE'
                          ? 'text-purple-600 dark:text-purple-400'
                          : currentTier === 'PRO'
                          ? 'text-amber-600 dark:text-amber-400'
                          : 'text-[var(--blue)]'
                      }`}
                    >
                      {user.tier}
                    </span>
                  </div>
                </div>
              </div>

              {/* Sign out */}
              <button
                onClick={logout}
                title="Sign Out"
                className="flex items-center gap-1 text-xs text-[var(--muted)] hover:text-red-400 p-1.5 sm:p-2 rounded-lg hover:bg-[var(--surface-hover)] transition-colors cursor-pointer"
              >
                <LogOut size={15} />
                <span className="hidden md:inline">Sign Out</span>
              </button>
            </div>
          ) : (
            <button
              onClick={openAuthModal}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--blue)] text-white text-xs font-semibold rounded-xl hover:opacity-90 transition-all shadow-sm cursor-pointer"
            >
              <LogIn size={14} />
              <span>Sign In</span>
            </button>
          )}
        </div>
      </header>

      {/* Pricing modal */}
      <PricingModal
        isOpen={isPricingOpen}
        onClose={() => setIsPricingOpen(false)}
        onUpgradeSuccess={handleUpgradeSuccess}
      />
    </>
  )
}
