'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import ThemeToggle from '@/components/layout/ThemeToggle'
import PricingModal from '@/components/billing/PricingModal'
import {
  TrendingUp,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  Lock,
  Scale,
  BarChart3,
  PieChart,
  Zap,
  Check,
  ChevronDown,
  Star,
  Crown,
  Layers,
  ArrowUpRight,
  Shield,
  HelpCircle,
} from 'lucide-react'

export default function LandingPage() {
  const { isAuthenticated, user, openAuthModal, refreshUser } = useAuth()
  const [isPricingOpen, setIsPricingOpen] = useState(false)
  const [activePreviewTab, setActivePreviewTab] = useState<'advisory' | 'tax' | 'risk' | 'sectors'>('advisory')
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  const toggleFaq = (index: number) => {
    setOpenFaq((prev) => (prev === index ? null : index))
  }

  const handlePricingClick = () => {
    if (isAuthenticated) {
      setIsPricingOpen(true)
    } else {
      openAuthModal()
    }
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] flex flex-col selection:bg-[var(--blue)] selection:text-white">
      {/* ── Top Announcement Banner ── */}
      <div className="bg-gradient-to-r from-blue-600/15 via-indigo-600/15 to-purple-600/15 border-b border-[var(--border)] px-4 py-2 text-center text-xs">
        <div className="inline-flex items-center gap-2 text-[var(--text)] font-medium">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[var(--blue)] text-white uppercase tracking-wider">
            Union Budget 2024
          </span>
          <span>FY 2024-25 STCG (20%) & LTCG (12.5%) Tax-Loss Harvesting Engine is Live</span>
          <a href="#features" className="underline text-[var(--blue)] hover:opacity-80 inline-flex items-center gap-0.5">
            Explore <ChevronDown size={12} className="-rotate-90" />
          </a>
        </div>
      </div>

      {/* ── Public Sticky Navigation ── */}
      <header className="sticky top-0 z-40 backdrop-blur-md bg-[var(--surface)]/90 border-b border-[var(--border)] px-4 sm:px-8 py-3.5 transition-colors">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
              <TrendingUp size={20} />
            </div>
            <div>
              <span className="font-extrabold text-base tracking-tight block">Portfolio Assistant</span>
              <span className="text-[10px] text-[var(--muted)] -mt-1 block font-medium">Multi-Tenant AI Advisory</span>
            </div>
          </Link>

          {/* Center Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-[var(--muted)]">
            <a href="#features" className="hover:text-[var(--text)] transition-colors">Features</a>
            <a href="#preview" className="hover:text-[var(--text)] transition-colors">Platform Demo</a>
            <a href="#pricing" className="hover:text-[var(--text)] transition-colors">Pricing</a>
            <a href="#faq" className="hover:text-[var(--text)] transition-colors">FAQ</a>
          </nav>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            <ThemeToggle />

            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[var(--blue)] hover:bg-blue-600 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
                >
                  <span>Go to Dashboard</span>
                  <ArrowRight size={14} />
                </Link>
              </div>
            ) : (
              <>
                <button
                  onClick={openAuthModal}
                  className="hidden sm:inline-flex items-center text-xs font-semibold text-[var(--text)] hover:text-[var(--blue)] px-3 py-1.5 transition-colors cursor-pointer"
                >
                  Sign In
                </button>
                <button
                  onClick={openAuthModal}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[var(--blue)] hover:bg-blue-600 text-white text-xs font-semibold rounded-xl shadow-sm transition-all cursor-pointer"
                >
                  <Sparkles size={13} />
                  <span>Get Started Free</span>
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero Section ── */}
      <section className="relative pt-12 sm:pt-20 pb-16 sm:pb-24 px-4 sm:px-6 overflow-hidden">
        {/* Background ambient glow circles */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] sm:w-[900px] h-[400px] bg-gradient-to-tr from-blue-500/10 via-indigo-500/10 to-purple-500/10 blur-3xl pointer-events-none rounded-full" />

        <div className="max-w-5xl mx-auto text-center relative z-10">
          {/* Tagline Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--surface)] border border-[var(--border)] text-xs font-medium text-[var(--muted)] mb-6 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[var(--text)] font-semibold">Institutional Quantitative Engine</span>
            <span className="text-[var(--muted)]">•</span>
            <span>Indian Equity Markets</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-[var(--text)] leading-[1.15] sm:leading-[1.12]">
            Institutional Portfolio Analytics <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-blue-400 dark:via-indigo-400 dark:to-purple-400 bg-clip-text text-transparent">
              Powered by Multi-Stage AI
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mt-5 text-sm sm:text-lg text-[var(--muted)] max-w-2xl mx-auto leading-relaxed">
            Connect Zerodha Kite with Fernet AES-256 client encryption. Execute 3-stage Gemini diagnostic audits, uncover capital gains tax savings before March 31st, and monitor quantitative risk metrics in real time.
          </p>

          {/* Dual CTAs */}
          <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            {isAuthenticated ? (
              <Link
                href="/dashboard"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-[var(--blue)] hover:bg-blue-600 text-white font-semibold text-sm rounded-xl shadow-lg shadow-blue-500/20 transition-all"
              >
                <span>Open Dashboard</span>
                <ArrowRight size={16} />
              </Link>
            ) : (
              <button
                onClick={openAuthModal}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-[var(--blue)] hover:bg-blue-600 text-white font-semibold text-sm rounded-xl shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
              >
                <Sparkles size={16} />
                <span>Get Started Free</span>
              </button>
            )}

            <Link
              href="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-[var(--surface)] hover:bg-[var(--surface-hover)] border border-[var(--border)] text-[var(--text)] font-semibold text-sm rounded-xl transition-all"
            >
              <span>Explore Live Dashboard</span>
              <ArrowUpRight size={16} className="text-[var(--muted)]" />
            </Link>
          </div>

          {/* Trust and Feature Badges Bar */}
          <div className="mt-12 pt-8 border-t border-[var(--border)] grid grid-cols-2 sm:grid-cols-4 gap-4 text-left">
            <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
              <p className="text-[11px] text-[var(--muted)] font-medium">Zerodha Sync</p>
              <p className="text-sm font-bold text-[var(--text)] mt-0.5">Fernet AES-256</p>
              <p className="text-[10px] text-emerald-500 mt-0.5">Encrypted at rest</p>
            </div>
            <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
              <p className="text-[11px] text-[var(--muted)] font-medium">Advisory Pipeline</p>
              <p className="text-sm font-bold text-[var(--text)] mt-0.5">3-Stage Gemini</p>
              <p className="text-[10px] text-[var(--blue)] mt-0.5">Health • Risk • Baskets</p>
            </div>
            <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
              <p className="text-[11px] text-[var(--muted)] font-medium">Tax Engine</p>
              <p className="text-sm font-bold text-[var(--text)] mt-0.5">Budget 2024-25</p>
              <p className="text-[10px] text-amber-500 mt-0.5">20% STCG / 12.5% LTCG</p>
            </div>
            <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
              <p className="text-[11px] text-[var(--muted)] font-medium">Quantitative Math</p>
              <p className="text-sm font-bold text-[var(--text)] mt-0.5">Beta & Sharpe</p>
              <p className="text-[10px] text-purple-500 mt-0.5">vs NIFTY 50 Benchmark</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Interactive Product Showcase ── */}
      <section id="preview" className="py-16 px-4 sm:px-6 bg-[var(--surface)] border-y border-[var(--border)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--blue)]">Interactive Showcase</span>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-1">
              Experience the Dashboard Capabilities
            </h2>
            <p className="text-xs sm:text-sm text-[var(--muted)] mt-2">
              Select any capability below to preview how Portfolio Assistant visualizes and evaluates your equity portfolio.
            </p>
          </div>

          {/* Showcase Tabs */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex p-1 bg-[var(--bg)] border border-[var(--border)] rounded-2xl overflow-x-auto max-w-full">
              {[
                { id: 'advisory', label: '🤖 AI Advisory', desc: '3-Stage Diagnostic' },
                { id: 'tax', label: '⚖️ Tax Harvesting', desc: 'Capital Gains Engine' },
                { id: 'risk', label: '📈 Quantitative Beta', desc: 'SEBI Benchmark' },
                { id: 'sectors', label: '🍕 Sector Allocation', desc: 'Concentration Caps' },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActivePreviewTab(t.id as any)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                    activePreviewTab === t.id
                      ? 'bg-[var(--surface)] text-[var(--text)] shadow-sm border border-[var(--border)]'
                      : 'text-[var(--muted)] hover:text-[var(--text)]'
                  }`}
                >
                  <span>{t.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Mock Frame */}
          <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg)] shadow-xl overflow-hidden p-4 sm:p-6 transition-all">
            {/* Mock Header Bar */}
            <div className="flex items-center justify-between pb-4 border-b border-[var(--border)] mb-5">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-red-400" />
                <span className="w-3 h-3 rounded-full bg-yellow-400" />
                <span className="w-3 h-3 rounded-full bg-green-400" />
                <span className="text-xs text-[var(--muted)] ml-2 font-mono">portfolio-assistant.local/dashboard</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span>Zerodha Live Sync</span>
              </div>
            </div>

            {/* Mock Content Based on Active Tab */}
            {activePreviewTab === 'advisory' && (
              <div className="flex flex-col gap-4 animate-in fade-in duration-300">
                <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-500">
                        HEALTH SCORE: 84/100
                      </span>
                      <span className="text-xs font-semibold">Stage 1 Diagnostic Passed</span>
                    </div>
                    <p className="text-xs text-[var(--muted)] mt-1">
                      Portfolio demonstrates resilient risk-adjusted characteristics with low single-stock concentration risk.
                    </p>
                  </div>
                  <span className="text-xs font-mono px-3 py-1 bg-[var(--bg)] border border-[var(--border)] rounded-lg text-[var(--muted)]">
                    Gemini 1.5 Flash
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-[var(--surface)] border border-emerald-500/30 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[var(--text)]">INFY • Infosys Ltd</span>
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500 text-white rounded">BUY / ADD</span>
                      </div>
                      <p className="text-xs text-[var(--muted)] mt-2">
                        IT sector weighting is 8% below target cap of 25%. High ROE (31.4%) and attractive valuation multiple relative to historical median.
                      </p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-[var(--border)] flex justify-between text-xs text-[var(--muted)]">
                      <span>Target Allocation: +2.5%</span>
                      <span>Execution Basket: Ready</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-[var(--surface)] border border-amber-500/30 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[var(--text)]">HDFCBANK • HDFC Bank</span>
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-500 text-black rounded">HOLD / TRIM</span>
                      </div>
                      <p className="text-xs text-[var(--muted)] mt-2">
                        Banking sector allocation currently stands at 27.2%, slightly breaching your 25% single-sector safety limit. Trim excess.
                      </p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-[var(--border)] flex justify-between text-xs text-[var(--muted)]">
                      <span>Safety Flag: Sector Overweight</span>
                      <span>Target Allocation: -2.2%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activePreviewTab === 'tax' && (
              <div className="flex flex-col gap-4 animate-in fade-in duration-300">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">Net STCG (&lt;1 yr)</p>
                    <p className="text-base font-bold text-[var(--text)] mt-0.5">₹48,200</p>
                    <p className="text-[10px] text-amber-500">20% tax = ₹9,640</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">Net LTCG (&gt;1 yr)</p>
                    <p className="text-base font-bold text-[var(--text)] mt-0.5">₹1,45,000</p>
                    <p className="text-[10px] text-[var(--blue)]">12.5% on excess</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">₹1.25L Exemption</p>
                    <p className="text-base font-bold text-emerald-500 mt-0.5">100% Utilised</p>
                    <p className="text-[10px] text-[var(--muted)]">₹1,25,000 tax-free</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">Harvestable Loss</p>
                    <p className="text-base font-bold text-red-500 mt-0.5">₹18,500</p>
                    <p className="text-[10px] text-emerald-500">Potential Saving: ₹3,700</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                  <div className="flex justify-between items-center text-xs mb-2">
                    <span className="font-semibold text-[var(--text)]">LTCG Annual Exemption Meter (Section 112A)</span>
                    <span className="text-[var(--muted)]">₹1,25,000 / ₹1,25,000</span>
                  </div>
                  <div className="w-full h-2.5 rounded-full bg-[var(--border)] overflow-hidden">
                    <div className="w-full h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full" />
                  </div>
                </div>
              </div>
            )}

            {activePreviewTab === 'risk' && (
              <div className="flex flex-col gap-4 animate-in fade-in duration-300">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">Portfolio Beta</p>
                    <p className="text-lg font-bold text-emerald-500 mt-0.5">0.94</p>
                    <p className="text-[10px] text-[var(--muted)]">Defensive vs Nifty 50</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">Sharpe Ratio</p>
                    <p className="text-lg font-bold text-[var(--text)] mt-0.5">1.82</p>
                    <p className="text-[10px] text-emerald-500">Above 7.1% G-Sec</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">Sortino Ratio</p>
                    <p className="text-lg font-bold text-[var(--text)] mt-0.5">2.41</p>
                    <p className="text-[10px] text-[var(--muted)]">Low downside risk</p>
                  </div>
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <p className="text-[11px] text-[var(--muted)]">Herfindahl (HHI)</p>
                    <p className="text-lg font-bold text-[var(--text)] mt-0.5">1,320</p>
                    <p className="text-[10px] text-emerald-500">Diversified (&lt; 1500)</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[var(--surface)] border border-[var(--border)] flex justify-between items-center text-xs">
                  <div>
                    <span className="font-semibold text-[var(--text)] block">SEBI Risk Classification</span>
                    <span className="text-[var(--muted)]">Calculated on historical volatility and weighted equity beta</span>
                  </div>
                  <span className="px-3 py-1 rounded-lg bg-[var(--bg)] border border-[var(--border)] font-bold text-[var(--text)]">
                    Moderate Risk
                  </span>
                </div>
              </div>
            )}

            {activePreviewTab === 'sectors' && (
              <div className="flex flex-col gap-4 animate-in fade-in duration-300">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold">Financial Services</span>
                      <span className="font-bold text-amber-500">27.2%</span>
                    </div>
                    <div className="w-full bg-[var(--border)] h-2 rounded-full mt-2 overflow-hidden">
                      <div className="bg-amber-500 h-full w-[108%]" />
                    </div>
                    <span className="text-[10px] text-amber-500 mt-1 block">Breaches 25% max cap</span>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold">Information Tech</span>
                      <span className="font-bold text-emerald-500">17.0%</span>
                    </div>
                    <div className="w-full bg-[var(--border)] h-2 rounded-full mt-2 overflow-hidden">
                      <div className="bg-emerald-500 h-full w-[68%]" />
                    </div>
                    <span className="text-[10px] text-emerald-500 mt-1 block">Within 25% safety cap</span>
                  </div>

                  <div className="p-3 rounded-xl bg-[var(--surface)] border border-[var(--border)]">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold">Auto & Ancillaries</span>
                      <span className="font-bold text-emerald-500">12.4%</span>
                    </div>
                    <div className="w-full bg-[var(--border)] h-2 rounded-full mt-2 overflow-hidden">
                      <div className="bg-emerald-500 h-full w-[49%]" />
                    </div>
                    <span className="text-[10px] text-emerald-500 mt-1 block">Within 25% safety cap</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── 4 Architectural Pillars Feature Grid ── */}
      <section id="features" className="py-20 px-4 sm:px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--blue)]">Engine Architecture</span>
            <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight mt-1 text-[var(--text)]">
              Four Pillars of Portfolio Intelligence
            </h2>
            <p className="text-xs sm:text-sm text-[var(--muted)] mt-2">
              Combining deterministic financial mathematics with multi-tenant LLM reasoning for institutional precision.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            {/* Pillar 1 */}
            <div className="p-6 sm:p-8 rounded-2xl bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between hover:border-[var(--blue)]/50 transition-all shadow-xs group">
              <div>
                <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                  <Sparkles size={24} />
                </div>
                <h3 className="text-lg font-bold text-[var(--text)] mb-2">
                  1. 3-Stage Gemini Advisory Pipeline
                </h3>
                <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed mb-4">
                  Runs an automated 3-prompt sequence: Stage 1 audits portfolio health, Stage 2 assigns deterministic risk flags against SEBI limits, and Stage 3 synthesizes staged BUY/SELL execution baskets.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-[var(--muted)] pt-4 border-t border-[var(--border)]">
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>Rule Engine fallback when LLM quotas or latency exceed limits</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>Configurable single-stock (5-50%) and sector caps (10-60%)</span>
                </li>
              </ul>
            </div>

            {/* Pillar 2 */}
            <div className="p-6 sm:p-8 rounded-2xl bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between hover:border-amber-500/50 transition-all shadow-xs group">
              <div>
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                  <Scale size={24} />
                </div>
                <h3 className="text-lg font-bold text-[var(--text)] mb-2">
                  2. Indian Tax-Loss Harvesting Engine
                </h3>
                <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed mb-4">
                  Compliant with Indian Union Budget 2024 revisions. Automatically calculates short-term capital gains at 20% and long-term gains at 12.5%, tracking Section 112A ₹1,25,000 exemption limits.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-[var(--muted)] pt-4 border-t border-[var(--border)]">
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>March 31st trade suggestions to harvest unrealized losses</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>FIFO-accurate holding period classification</span>
                </li>
              </ul>
            </div>

            {/* Pillar 3 */}
            <div className="p-6 sm:p-8 rounded-2xl bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between hover:border-emerald-500/50 transition-all shadow-xs group">
              <div>
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                  <ShieldCheck size={24} />
                </div>
                <h3 className="text-lg font-bold text-[var(--text)] mb-2">
                  3. Encrypted Broker Integration
                </h3>
                <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed mb-4">
                  Connect Zerodha Kite in seconds via API or session enctoken. Your credentials are encrypted at rest with Fernet AES-256 symmetric keys, ensuring zero-knowledge isolation.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-[var(--muted)] pt-4 border-t border-[var(--border)]">
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>Tenant-isolated database schema with Google IAM OAuth 2.0</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>One-click session disconnect and credential purging</span>
                </li>
              </ul>
            </div>

            {/* Pillar 4 */}
            <div className="p-6 sm:p-8 rounded-2xl bg-[var(--surface)] border border-[var(--border)] flex flex-col justify-between hover:border-purple-500/50 transition-all shadow-xs group">
              <div>
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-500 flex items-center justify-center mb-5 group-hover:scale-105 transition-transform">
                  <BarChart3 size={24} />
                </div>
                <h3 className="text-lg font-bold text-[var(--text)] mb-2">
                  4. Institutional Quantitative Ratios
                </h3>
                <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed mb-4">
                  Go beyond simple P&L. Compute cash-flow accurate XIRR, Portfolio Beta relative to NIFTY 50 / SENSEX, Sharpe and Sortino ratios against 10Y Indian G-Sec, and Herfindahl concentration indexes.
                </p>
              </div>
              <ul className="space-y-2 text-xs text-[var(--muted)] pt-4 border-t border-[var(--border)]">
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>High-performance Redis caching for market indices</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check size={14} className="text-emerald-500 shrink-0" />
                  <span>Sub-200ms vectorized analytics computations</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── Pricing & SaaS Tiers Section ── */}
      <section id="pricing" className="py-20 px-4 sm:px-6 bg-[var(--surface)] border-t border-[var(--border)]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-14">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--blue)]">Transparent Plans</span>
            <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight mt-1 text-[var(--text)]">
              Choose the Right Plan for Your Wealth
            </h2>
            <p className="text-xs sm:text-sm text-[var(--muted)] mt-2">
              Start free with core quantitative metrics, or upgrade to PRO to unlock automated tax harvesting and AI rebalancing baskets.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8 items-stretch">
            {/* Free Plan */}
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg)] p-6 sm:p-8 flex flex-col justify-between shadow-xs">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Zap size={20} className="text-[var(--muted)]" />
                  <span className="font-bold text-base text-[var(--text)]">FREE</span>
                </div>
                <div className="flex items-baseline gap-1 mb-5">
                  <span className="text-3xl font-extrabold text-[var(--text)]">₹0</span>
                  <span className="text-xs text-[var(--muted)]">/ month</span>
                </div>
                <p className="text-xs text-[var(--muted)] mb-6">
                  Essential portfolio tracking and fundamental risk metrics for individual retail investors.
                </p>
                <ul className="space-y-3 text-xs text-[var(--muted)]">
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>1 Broker connection (Zerodha)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Core metrics (XIRR, Beta, Sharpe)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>5 AI Advisory runs / month</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Sector cap guardrails</span>
                  </li>
                </ul>
              </div>

              <button
                onClick={openAuthModal}
                className="mt-8 w-full py-2.5 px-4 rounded-xl border border-[var(--border)] text-xs font-semibold text-[var(--text)] hover:bg-[var(--surface-hover)] transition-all cursor-pointer"
              >
                {isAuthenticated ? 'Active Plan' : 'Get Started Free'}
              </button>
            </div>

            {/* Pro Plan (Highlighted) */}
            <div className="relative rounded-2xl border-2 border-amber-400 bg-[var(--bg)] p-6 sm:p-8 flex flex-col justify-between shadow-xl ring-2 ring-amber-400/20">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-amber-400 text-black text-[10px] font-bold rounded-full uppercase tracking-wider shadow">
                Most Popular
              </span>

              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Star size={20} className="text-amber-400 fill-amber-400" />
                  <span className="font-bold text-base text-[var(--text)]">PRO</span>
                </div>
                <div className="flex items-baseline gap-1 mb-5">
                  <span className="text-3xl font-extrabold text-[var(--text)]">₹299</span>
                  <span className="text-xs text-[var(--muted)]">/ month</span>
                </div>
                <p className="text-xs text-[var(--muted)] mb-6">
                  For serious investors seeking active capital gains tax harvesting and continuous AI advisory.
                </p>
                <ul className="space-y-3 text-xs text-[var(--text)]">
                  <li className="flex items-center gap-2 font-medium">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Everything in Free</span>
                  </li>
                  <li className="flex items-center gap-2 font-medium">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Indian Tax-Loss Harvesting Engine</span>
                  </li>
                  <li className="flex items-center gap-2 font-medium">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>50 AI Advisory runs / month</span>
                  </li>
                  <li className="flex items-center gap-2 font-medium">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Automated Zerodha basket export</span>
                  </li>
                  <li className="flex items-center gap-2 font-medium">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Priority rebalancing notifications</span>
                  </li>
                </ul>
              </div>

              <button
                onClick={handlePricingClick}
                className="mt-8 w-full py-2.5 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 text-black text-xs font-bold transition-all shadow-md cursor-pointer"
              >
                Upgrade to Pro
              </button>
            </div>

            {/* Elite Plan */}
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--bg)] p-6 sm:p-8 flex flex-col justify-between shadow-xs">
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Crown size={20} className="text-purple-400" />
                  <span className="font-bold text-base text-[var(--text)]">ELITE</span>
                </div>
                <div className="flex items-baseline gap-1 mb-5">
                  <span className="text-3xl font-extrabold text-[var(--text)]">₹799</span>
                  <span className="text-xs text-[var(--muted)]">/ month</span>
                </div>
                <p className="text-xs text-[var(--muted)] mb-6">
                  Unrestricted power for HNIs, family offices, and multi-broker wealth portfolios.
                </p>
                <ul className="space-y-3 text-xs text-[var(--muted)]">
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Everything in Pro</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Multi-broker connection sync</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Unlimited AI Advisory runs</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Custom risk benchmark modeling</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <Check size={14} className="text-emerald-500 shrink-0" />
                    <span>Early access to new financial algorithms</span>
                  </li>
                </ul>
              </div>

              <button
                onClick={handlePricingClick}
                className="mt-8 w-full py-2.5 px-4 rounded-xl bg-[var(--blue)] hover:bg-blue-600 text-white text-xs font-semibold transition-all shadow-sm cursor-pointer"
              >
                Upgrade to Elite
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── FAQ Section ── */}
      <section id="faq" className="py-20 px-4 sm:px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--blue)]">Questions & Answers</span>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-1 text-[var(--text)]">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="space-y-3">
            {[
              {
                q: 'How does Zerodha integration work, and is my password required?',
                a: 'You never provide your Zerodha account password. Portfolio Assistant integrates using Zerodha Kite Connect login or your temporary enctoken session cookie. All session tokens are encrypted at rest using Fernet AES-256 keys and are never exposed to other tenants.',
              },
              {
                q: 'How does the Indian Tax-Loss Harvesting engine calculate capital gains?',
                a: 'The engine implements the latest rules following the Indian Finance Act (Union Budget 2024 revisions): Equity holdings under 365 days are taxed at 20% (STCG), and holdings over 365 days are taxed at 12.5% (LTCG) with Section 112A ₹1,25,000 exemption tracking. Before March 31st, it identifies holdings with unrealized losses that can be harvested to lower your net tax payable.',
              },
              {
                q: 'What is the 3-Stage Google Gemini AI Advisory pipeline?',
                a: 'Stage 1 evaluates your overall portfolio health against your investment goal. Stage 2 executes deterministic checks against sector and stock caps to generate safety flags. Stage 3 synthesizes specific, risk-weighted rebalancing recommendations that can be staged into Zerodha execution baskets.',
              },
              {
                q: 'Is my financial portfolio data used to train AI models?',
                a: 'No. Your portfolio holdings and user data are strictly isolated and never used for training foundation models. AI prompts are executed transiently via Google Cloud Gemini enterprise APIs with strict data privacy guarantees.',
              },
              {
                q: 'Can I cancel or change my plan anytime?',
                a: 'Yes. Upgrades and plan changes take effect immediately. You can cancel at any time, and you will retain access to your plan features until the end of the current billing cycle.',
              },
            ].map((item, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden transition-all"
              >
                <button
                  onClick={() => toggleFaq(idx)}
                  className="w-full p-4 sm:p-5 text-left flex items-center justify-between gap-4 font-semibold text-xs sm:text-sm text-[var(--text)] hover:bg-[var(--surface-hover)] transition-colors cursor-pointer"
                >
                  <span>{item.q}</span>
                  <ChevronDown
                    size={16}
                    className={`text-[var(--muted)] transition-transform duration-200 shrink-0 ${
                      openFaq === idx ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {openFaq === idx && (
                  <div className="px-4 sm:px-5 pb-4 sm:pb-5 text-xs sm:text-sm text-[var(--muted)] leading-relaxed border-t border-[var(--border)] pt-3 animate-in fade-in duration-150">
                    {item.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="mt-auto border-t border-[var(--border)] bg-[var(--surface)] px-4 sm:px-8 py-10">
        <div className="max-w-6xl mx-auto flex flex-col gap-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-[var(--blue)]/10 text-[var(--blue)] flex items-center justify-center">
                <TrendingUp size={18} />
              </div>
              <span className="font-bold text-sm tracking-tight">Portfolio Assistant</span>
            </div>

            <div className="flex items-center gap-6 text-xs text-[var(--muted)]">
              <a href="#features" className="hover:text-[var(--text)] transition-colors">Features</a>
              <a href="#preview" className="hover:text-[var(--text)] transition-colors">Demo</a>
              <a href="#pricing" className="hover:text-[var(--text)] transition-colors">Pricing</a>
              <Link href="/dashboard" className="hover:text-[var(--text)] transition-colors">Dashboard</Link>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)] text-[10px] text-[var(--muted)] leading-relaxed">
            <p className="font-semibold text-[var(--text)] mb-1">Regulatory & Educational Notice:</p>
            Portfolio Assistant is a financial technology software tool designed for quantitative analysis, tax loss planning, and informational insights. It is not a SEBI-registered Investment Adviser (RIA) or Research Analyst (RA). The automated suggestions and AI diagnostic outputs do not constitute personalized investment advice or an endorsement to buy or sell securities. Investments in the securities market are subject to market risks; read all related documents carefully before investing.
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between text-[11px] text-[var(--muted)] gap-2">
            <p>© {new Date().getFullYear()} Portfolio Assistant. Built with Next.js & Google Gemini.</p>
            <p>End-to-End Multi-Tenant Isolation • AES-256 Encrypted</p>
          </div>
        </div>
      </footer>

      {/* ── Pricing Modal ── */}
      <PricingModal
        isOpen={isPricingOpen}
        onClose={() => setIsPricingOpen(false)}
        onUpgradeSuccess={async () => {
          await refreshUser()
        }}
      />
    </div>
  )
}
