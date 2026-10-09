'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '@/lib/auth-context'
import { X, Mail, Lock, User as UserIcon, AlertCircle, Loader2, Sparkles } from 'lucide-react'

declare global {
  interface Window {
    google?: any
  }
}

export default function AuthModal() {
  const {
    isAuthModalOpen,
    closeAuthModal,
    loginWithGoogle,
    loginWithEmail,
    register,
  } = useAuth()

  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isGsiReady, setIsGsiReady] = useState(false)
  const googleButtonRef = useRef<HTMLDivElement>(null)

  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''

  const handleGoogleCredentialResponse = useCallback(async (response: any) => {
    if (!response?.credential) return
    setError(null)
    setIsSubmitting(true)
    try {
      await loginWithGoogle(response.credential)
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Google Sign-In failed'
      setError(detail)
    } finally {
      setIsSubmitting(false)
    }
  }, [loginWithGoogle])

  useEffect(() => {
    if (isAuthModalOpen) {
      setError(null)
    }
  }, [isAuthModalOpen, mode])

  // Initialize Google Identity Services when available
  useEffect(() => {
    if (!isAuthModalOpen || !googleClientId) return

    const initGsi = () => {
      if (typeof window !== 'undefined' && window.google?.accounts?.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: googleClientId,
            callback: handleGoogleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true,
          })

          if (googleButtonRef.current) {
            const btnWidth = typeof window !== 'undefined' ? Math.min(320, Math.max(220, window.innerWidth - 64)) : 300
            window.google.accounts.id.renderButton(googleButtonRef.current, {
              theme: 'outline',
              size: 'large',
              width: btnWidth,
              text: 'continue_with',
              shape: 'rectangular',
              logo_alignment: 'left',
            })
            setIsGsiReady(true)
          }
        } catch (e) {
          console.warn('Google GSI initialization error:', e)
        }
      }
    }

    if (window.google?.accounts?.id) {
      initGsi()
    } else {
      const timer = setInterval(() => {
        if (window.google?.accounts?.id) {
          initGsi()
          clearInterval(timer)
        }
      }, 300)
      return () => clearInterval(timer)
    }
  }, [isAuthModalOpen, googleClientId, handleGoogleCredentialResponse])

  if (!isAuthModalOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      if (mode === 'login') {
        await loginWithEmail(email, password)
      } else {
        await register(email, password, fullName)
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Authentication failed'
      setError(detail)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleManualGoogleClick = async () => {
    setError(null)
    setIsSubmitting(true)
    try {
      if (googleClientId && typeof window !== 'undefined' && window.google?.accounts?.id) {
        window.google.accounts.id.prompt((notification: any) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            console.log('Google One-Tap not displayed; please click the Google button directly')
          }
        })
      } else {
        setError('Google Client ID is not configured. Please check your NEXT_PUBLIC_GOOGLE_CLIENT_ID environment variable.')
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Google Sign-In failed'
      setError(detail)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md max-h-[92vh] overflow-y-auto bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl p-4 sm:p-6 flex flex-col gap-4 sm:gap-5 text-[var(--text)]">
        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 text-[var(--muted)] hover:text-[var(--text)] transition-colors p-1 rounded-lg hover:bg-[var(--surface-hover)] cursor-pointer"
        >
          <X size={18} />
        </button>

        {/* Modal Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[var(--blue)]/10 text-[var(--blue)] mb-3">
            <Sparkles size={24} />
          </div>
          <h2 className="text-xl font-bold tracking-tight">
            {mode === 'login' ? 'Welcome Back' : 'Create Your Account'}
          </h2>
          <p className="text-xs text-[var(--muted)] mt-1">
            {mode === 'login'
              ? 'Sign in to access your tenant-isolated portfolio & AI advisor'
              : 'Sign up for free to unlock AI portfolio diagnostics & multi-broker sync'}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded-xl text-xs">
            <AlertCircle size={15} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Google IAM Sign-In Section */}
        <div className="flex flex-col items-center gap-2 w-full">
          {/* Container for Official Google Button if GSI renders */}
          {googleClientId && (
            <div
              ref={googleButtonRef}
              className={`w-full flex justify-center ${isGsiReady ? 'block' : 'hidden'}`}
            />
          )}

          {/* Standard Fallback / Primary Google Button (always shown if GSI isn't ready or in dev) */}
          {(!googleClientId || !isGsiReady) && (
            <button
              type="button"
              onClick={handleManualGoogleClick}
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-3 py-2.5 px-4 bg-[var(--bg)] border border-[var(--border)] hover:border-[var(--muted)] rounded-xl font-medium text-xs text-[var(--text)] transition-all hover:shadow-sm disabled:opacity-50 cursor-pointer"
            >
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>
          )}
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-[var(--border)]" />
          <span className="text-[10px] text-[var(--muted)] uppercase tracking-wider">or with email</span>
          <div className="flex-1 h-px bg-[var(--border)]" />
        </div>

        {/* Email / Password Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          {mode === 'register' && (
            <div>
              <label className="text-xs text-[var(--muted)] mb-1 block">Full Name</label>
              <div className="relative">
                <UserIcon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
                <input
                  type="text"
                  placeholder="Your full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-[var(--bg)] border border-[var(--border)] focus:border-[var(--blue)] rounded-xl pl-9 pr-3 py-2 text-xs outline-none transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="text-xs text-[var(--muted)] mb-1 block">Email Address</label>
            <div className="relative">
              <Mail size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[var(--bg)] border border-[var(--border)] focus:border-[var(--blue)] rounded-xl pl-9 pr-3 py-2 text-xs outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-[var(--muted)] mb-1 block">Password</label>
            <div className="relative">
              <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
              <input
                type="password"
                required
                minLength={6}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[var(--bg)] border border-[var(--border)] focus:border-[var(--blue)] rounded-xl pl-9 pr-3 py-2 text-xs outline-none transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 w-full flex items-center justify-center gap-2 py-2.5 bg-[var(--blue)] text-white font-medium rounded-xl text-xs hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
          >
            {isSubmitting ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Please wait…
              </>
            ) : mode === 'login' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        {/* Toggle Mode */}
        <div className="text-center text-xs text-[var(--muted)]">
          {mode === 'login' ? (
            <>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => setMode('register')}
                className="text-[var(--blue)] font-semibold hover:underline cursor-pointer"
              >
                Sign Up
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => setMode('login')}
                className="text-[var(--blue)] font-semibold hover:underline cursor-pointer"
              >
                Sign In
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
