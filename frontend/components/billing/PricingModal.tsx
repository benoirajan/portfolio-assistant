'use client'

import { useEffect, useState, useCallback } from 'react'
import { X, Check, Zap, Star, Crown } from 'lucide-react'
import type { BillingPlan } from '@/lib/types'
import {
  fetchBillingPlans,
  createBillingOrder,
  verifyBillingPayment,
} from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

interface PricingModalProps {
  isOpen: boolean
  onClose: () => void
  /** Called after a successful upgrade so the parent can refresh user state */
  onUpgradeSuccess: (newTier: string) => void
}

const TIER_ICONS: Record<string, React.ReactNode> = {
  FREE: <Zap size={20} className="text-[var(--muted)]" />,
  PRO: <Star size={20} className="text-amber-400" />,
  ELITE: <Crown size={20} className="text-purple-400" />,
}

const TIER_BORDER: Record<string, string> = {
  FREE: 'border-[var(--border)]',
  PRO: 'border-amber-400 ring-2 ring-amber-400/30',
  ELITE: 'border-purple-400',
}

export default function PricingModal({
  isOpen,
  onClose,
  onUpgradeSuccess,
}: PricingModalProps) {
  const { user, refreshUser } = useAuth()
  const [plans, setPlans] = useState<BillingPlan[]>([])
  const [loadingPlans, setLoadingPlans] = useState(false)
  const [upgradingTier, setUpgradingTier] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadPlans = useCallback(async () => {
    setLoadingPlans(true)
    try {
      const res = await fetchBillingPlans()
      setPlans(res.plans)
    } catch {
      setError('Failed to load plans. Please try again.')
    } finally {
      setLoadingPlans(false)
    }
  }, [])

  useEffect(() => {
    if (isOpen) {
      loadPlans()
      setError(null)
    }
  }, [isOpen, loadPlans])

  const handleUpgrade = async (targetTier: string) => {
    setError(null)
    setUpgradingTier(targetTier)
    try {
      const orderRes = await createBillingOrder(targetTier)

      if (orderRes.mock_mode) {
        // ── Mock mode: simulate a completed payment without Razorpay widget ──
        const mockPaymentId = `pay_MOCK_${Date.now()}`
        const verifyRes = await verifyBillingPayment({
          razorpay_order_id: orderRes.razorpay_order_id,
          razorpay_payment_id: mockPaymentId,
          razorpay_signature: 'mock_signature',
          target_tier: targetTier,
        })
        await refreshUser()
        onUpgradeSuccess(verifyRes.tier)
        onClose()
      } else {
        // ── Live mode: open Razorpay checkout widget ──
        // @ts-expect-error — Razorpay is loaded via <Script> in the page layout
        const rzp = new window.Razorpay({
          key: orderRes.key_id,
          amount: orderRes.amount,
          currency: orderRes.currency,
          order_id: orderRes.razorpay_order_id,
          name: 'Portfolio Assistant',
          description: `Upgrade to ${targetTier} Plan`,
          prefill: {
            email: user?.email ?? '',
            name: user?.full_name ?? '',
          },
          handler: async (response: {
            razorpay_order_id: string
            razorpay_payment_id: string
            razorpay_signature: string
          }) => {
            try {
              const verifyRes = await verifyBillingPayment({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
                target_tier: targetTier,
              })
              await refreshUser()
              onUpgradeSuccess(verifyRes.tier)
              onClose()
            } catch (err: any) {
              setError(err?.response?.data?.detail ?? 'Payment verification failed.')
            }
          },
          modal: {
            ondismiss: () => setUpgradingTier(null),
          },
        })
        rzp.open()
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Upgrade failed. Please try again.')
    } finally {
      setUpgradingTier(null)
    }
  }

  if (!isOpen) return null

  const currentTier = (user?.tier ?? 'FREE').toUpperCase()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-3 sm:p-4">
      <div className="relative w-full max-w-3xl max-h-[92vh] flex flex-col bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 sm:px-6 py-4 sm:py-5 border-b border-[var(--border)] shrink-0">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[var(--text)]">Choose Your Plan</h2>
            <p className="text-[11px] sm:text-xs text-[var(--muted)] mt-0.5">
              Upgrade to unlock AI advisory runs, tax harvesting & more.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-[var(--surface-hover)] text-[var(--muted)] hover:text-[var(--text)] transition-colors cursor-pointer"
          >
            <X size={18} />
          </button>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mx-5 sm:mx-6 mt-4 px-4 py-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
            {error}
          </div>
        )}

        {/* Plans grid */}
        <div className="overflow-y-auto p-4 sm:p-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {loadingPlans
            ? [1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-64 rounded-xl bg-[var(--bg)] border border-[var(--border)] animate-pulse"
                />
              ))
            : plans.map((plan) => {
                const isCurrent = plan.tier === currentTier
                const isUpgrading = upgradingTier === plan.tier

                return (
                  <div
                    key={plan.tier}
                    className={`relative flex flex-col rounded-xl border bg-[var(--bg)] p-5 transition-all ${TIER_BORDER[plan.tier]}`}
                  >
                    {/* Popular badge */}
                    {plan.highlight && (
                      <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-amber-400 text-black text-[10px] font-bold rounded-full uppercase tracking-wider shadow">
                        Most Popular
                      </span>
                    )}

                    {/* Tier header */}
                    <div className="flex items-center gap-2 mb-3">
                      {TIER_ICONS[plan.tier]}
                      <span className="font-bold text-[var(--text)] text-sm">{plan.tier}</span>
                    </div>

                    {/* Price */}
                    <div className="mb-4">
                      {plan.price_inr === 0 ? (
                        <span className="text-2xl font-extrabold text-[var(--text)]">Free</span>
                      ) : (
                        <div className="flex items-baseline gap-1">
                          <span className="text-2xl font-extrabold text-[var(--text)]">
                            ₹{plan.price_inr}
                          </span>
                          <span className="text-xs text-[var(--muted)]">/ month</span>
                        </div>
                      )}
                    </div>

                    {/* Features */}
                    <ul className="flex-1 space-y-1.5 mb-5">
                      {plan.features.map((feat) => (
                        <li key={feat} className="flex items-start gap-2 text-xs text-[var(--muted)]">
                          <Check size={12} className="text-[var(--green)] mt-0.5 flex-shrink-0" />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>

                    {/* CTA */}
                    {isCurrent ? (
                      <div className="text-center text-xs font-semibold text-[var(--muted)] py-2 border border-[var(--border)] rounded-lg">
                        Current Plan
                      </div>
                    ) : plan.price_inr === 0 ? (
                      <div className="text-center text-xs text-[var(--muted)] py-2">
                        Default
                      </div>
                    ) : (
                      <button
                        disabled={isUpgrading || upgradingTier !== null}
                        onClick={() => handleUpgrade(plan.tier)}
                        className={`w-full py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer
                          ${plan.highlight
                            ? 'bg-amber-400 text-black hover:bg-amber-300'
                            : 'bg-[var(--blue)] text-white hover:opacity-90'
                          }
                          disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        {isUpgrading ? 'Processing…' : `Upgrade to ${plan.tier}`}
                      </button>
                    )}
                  </div>
                )
              })}
          </div>
        </div>

        {/* Footer note */}
        <div className="px-6 pb-5 text-center text-[10px] text-[var(--muted)]">
          {process.env.NEXT_PUBLIC_RAZORPAY_MOCK === 'true'
            ? '⚠️ Mock payment mode — no real charges will be made.'
            : 'Payments are processed securely via Razorpay. Cancel anytime.'}
        </div>
      </div>
    </div>
  )
}
