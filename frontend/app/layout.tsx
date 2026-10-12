'use client'

import Script from 'next/script'
import './globals.css'
import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme/ThemeProvider'
import { AuthProvider } from '@/lib/auth-context'
import AuthModal from '@/components/auth/AuthModal'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        retry: 1,
        refetchOnWindowFocus: false,
      }
    }
  }))

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <title>FolioGuard — AI Portfolio Analytics & Risk Intelligence</title>
        <meta
          name="description"
          content="FolioGuard: Institutional-grade equity analytics, Union Budget 2024-25 tax-loss harvesting, and multi-stage AI advisory for Zerodha investors."
        />
      </head>
      <body>
        <Script
          src="https://accounts.google.com/gsi/client"
          strategy="afterInteractive"
        />
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange={false}
        >
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              {children}
              <AuthModal />
            </AuthProvider>
          </QueryClientProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

