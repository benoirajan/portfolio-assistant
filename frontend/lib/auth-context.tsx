'use client'

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { User, BrokerStatus, RegisterResponse, ResendOtpResponse } from './types'
import {
  fetchCurrentUser,
  loginWithGoogle as apiLoginGoogle,
  loginWithEmail as apiLoginEmail,
  registerUser as apiRegisterUser,
  verifyEmailOtp as apiVerifyEmailOtp,
  resendEmailOtp as apiResendEmailOtp,
  saveBrokerEnctoken as apiSaveBrokerEnctoken,
  disconnectBroker as apiDisconnectBroker,
} from './api'

interface AuthContextType {
  user: User | null
  token: string | null
  brokerStatus: BrokerStatus | null
  isAuthenticated: boolean
  isLoading: boolean
  isAuthModalOpen: boolean
  openAuthModal: () => void
  closeAuthModal: () => void
  loginWithGoogle: (credential: string) => Promise<void>
  loginWithEmail: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<RegisterResponse>
  verifyOtp: (email: string, otp: string) => Promise<void>
  resendOtp: (email: string) => Promise<ResendOtpResponse>
  logout: () => void
  saveEnctoken: (enctoken: string) => Promise<void>
  disconnectBrokerSession: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [brokerStatus, setBrokerStatus] = useState<BrokerStatus | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false)

  const openAuthModal = useCallback(() => setIsAuthModalOpen(true), [])
  const closeAuthModal = useCallback(() => setIsAuthModalOpen(false), [])

  const logout = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('enctoken')
    }
    setToken(null)
    setUser(null)
    setBrokerStatus(null)
  }, [])

  const refreshUser = useCallback(async () => {
    const savedToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (!savedToken) {
      setUser(null)
      setBrokerStatus(null)
      setIsLoading(false)
      return
    }

    try {
      const res = await fetchCurrentUser()
      setUser(res.user)
      setBrokerStatus(res.broker_status)
    } catch (err: any) {
      if (err?.response?.status !== 401) {
        console.warn('Failed to fetch current user profile:', err)
      }
      logout()
    } finally {
      setIsLoading(false)
    }
  }, [logout])

  useEffect(() => {
    const savedToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (savedToken) {
      setToken(savedToken)
      refreshUser()
    } else {
      setIsLoading(false)
    }

    const handleUnauthorized = () => {
      logout()
    }
    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [refreshUser, logout])

  const loginWithGoogle = useCallback(async (credential: string) => {
    setIsLoading(true)
    try {
      const res = await apiLoginGoogle(credential)
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', res.access_token)
      }
      setToken(res.access_token)
      setUser(res.user)
      setIsAuthModalOpen(false)
      await refreshUser()
    } finally {
      setIsLoading(false)
    }
  }, [refreshUser])

  const loginWithEmail = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const res = await apiLoginEmail(email, password)
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', res.access_token)
      }
      setToken(res.access_token)
      setUser(res.user)
      setIsAuthModalOpen(false)
      await refreshUser()
    } finally {
      setIsLoading(false)
    }
  }, [refreshUser])

  const register = useCallback(async (email: string, password: string, fullName?: string): Promise<RegisterResponse> => {
    setIsLoading(true)
    try {
      return await apiRegisterUser(email, password, fullName)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const verifyOtp = useCallback(async (email: string, otp: string) => {
    setIsLoading(true)
    try {
      const res = await apiVerifyEmailOtp(email, otp)
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth_token', res.access_token)
      }
      setToken(res.access_token)
      setUser(res.user)
      setIsAuthModalOpen(false)
      await refreshUser()
    } finally {
      setIsLoading(false)
    }
  }, [refreshUser])

  const resendOtp = useCallback(async (email: string): Promise<ResendOtpResponse> => {
    return await apiResendEmailOtp(email)
  }, [])

  const saveEnctoken = useCallback(async (enctoken: string) => {
    const res = await apiSaveBrokerEnctoken(enctoken)
    if (typeof window !== 'undefined') {
      localStorage.setItem('enctoken', enctoken)
    }
    setBrokerStatus({ has_enctoken: res.has_enctoken, broker: 'ZERODHA' })
  }, [])

  const disconnectBrokerSession = useCallback(async () => {
    await apiDisconnectBroker()
    if (typeof window !== 'undefined') {
      localStorage.removeItem('enctoken')
    }
    setBrokerStatus({ has_enctoken: false, broker: null })
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        brokerStatus,
        isAuthenticated: !!user && !!token,
        isLoading,
        isAuthModalOpen,
        openAuthModal,
        closeAuthModal,
        loginWithGoogle,
        loginWithEmail,
        register,
        verifyOtp,
        resendOtp,
        logout,
        saveEnctoken,
        disconnectBrokerSession,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

