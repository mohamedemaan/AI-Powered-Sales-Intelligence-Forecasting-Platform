'use client'

import React, { ReactNode, useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Sidebar } from './Sidebar'
import { useAuth } from '../../hooks/useAuth'
import { Loader2 } from 'lucide-react'

const PUBLIC_ROUTES = ['/', '/login', '/landing']

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, loading } = useAuth()

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname)

  useEffect(() => {
    // If not loading, user is unauthenticated, and attempting to access a protected dashboard route
    if (!loading && !user && !isPublicRoute) {
      router.push('/login')
    }
  }, [loading, user, isPublicRoute, router])

  // Public standalone pages (Welcome Page, Login/Register)
  if (isPublicRoute) {
    return <>{children}</>
  }

  // Loading state while verifying authentication token on protected routes
  if (loading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm font-medium tracking-wide text-slate-300">
            Initializing SalesMind AI Workspace...
          </p>
        </div>
      </div>
    )
  }

  // If unauthenticated on protected route, show redirecting state until router completes push
  if (!user) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <p className="text-sm text-slate-300">Redirecting to sign in...</p>
        </div>
      </div>
    )
  }

  // Authenticated Dashboard Layout
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8">
        {children}
      </main>
    </div>
  )
}
