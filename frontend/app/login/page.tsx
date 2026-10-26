'use client'

import React, { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '../../hooks/useAuth'
import { ArrowLeft, Sparkles, ShieldCheck, Lock, Mail, ArrowRight } from 'lucide-react'

function LoginFormContent() {
  const searchParams = useSearchParams()
  const initialMode = searchParams.get('mode') === 'register'
  const [isRegister, setIsRegister] = useState(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { login, register, logout, user } = useAuth()

  useEffect(() => {
    if (searchParams.get('mode') === 'register') {
      setIsRegister(true)
    } else if (searchParams.get('mode') === 'login') {
      setIsRegister(false)
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)

    if (isRegister) {
      if (password.length < 12) {
        setErrorMsg('Password must be at least 12 characters.')
        return
      }
      if (!/[A-Z]/.test(password)) {
        setErrorMsg('Password must contain at least one uppercase letter (A-Z).')
        return
      }
      if (!/[a-z]/.test(password)) {
        setErrorMsg('Password must contain at least one lowercase letter (a-z).')
        return
      }
      if (!/[0-9]/.test(password)) {
        setErrorMsg('Password must contain at least one number (0-9).')
        return
      }
      if (!/[\W_]/.test(password)) {
        setErrorMsg('Password must contain at least one special character (!@#$%^&* etc).')
        return
      }
    }

    setSubmitting(true)

    const result = isRegister 
      ? await register(email, password)
      : await login(email, password)

    if (!result.success) {
      const err = typeof result.error === 'string' ? result.error : 'Authentication failed. Please verify credentials.'
      setErrorMsg(err)
    }
    setSubmitting(false)
  }

  // If already logged in, show active session card
  if (user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen px-4 py-12 bg-background">
        <div className="w-full max-w-md bg-surface p-8 rounded-2xl border border-slate-700 shadow-2xl space-y-6 text-center">
          <div className="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold shadow-inner">
            {user.email.charAt(0).toUpperCase()}
          </div>
          
          <div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 inline-flex items-center gap-1.5 mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Authenticated Session
            </span>
            <h2 className="text-2xl font-bold text-white">Welcome Back</h2>
            <p className="text-sm text-slate-400 mt-1 truncate">{user.email}</p>
          </div>

          <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-800 text-left space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Assigned Role:</span>
              <span className="text-primary font-mono font-semibold bg-primary/10 px-2 py-0.5 rounded">
                {user.role}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Account Status:</span>
              <span className="text-emerald-400 font-semibold">{user.is_active ? 'Active' : 'Inactive'}</span>
            </div>
            {user.tenant_id && (
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Tenant Workspace:</span>
                <span className="text-slate-300 font-mono text-[11px]">{user.tenant_id.slice(0, 8)}...</span>
              </div>
            )}
          </div>

          <div className="space-y-3 pt-2">
            <Link
              href="/dashboard"
              className="w-full bg-primary hover:bg-blue-600 text-white p-3 rounded-xl font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20"
            >
              <span>Launch Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <div className="flex gap-2">
              <Link
                href="/"
                className="flex-1 text-center text-xs font-medium py-2.5 px-3 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
              >
                Welcome Page
              </Link>
              <button
                onClick={logout}
                className="flex-1 text-center text-xs font-medium py-2.5 px-3 rounded-lg bg-slate-800 text-slate-400 hover:text-danger hover:bg-slate-750 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-12 bg-background relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10 space-y-6">
        {/* Navigation link back to Welcome Page */}
        <div className="flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-white transition group"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition" />
            <span>Back to Welcome Page</span>
          </Link>
          <span className="text-xs font-mono text-cyan-400 font-semibold tracking-wide">
            SalesMind AI
          </span>
        </div>

        {/* Authentication Card */}
        <div className="bg-surface/90 backdrop-blur-xl p-8 rounded-2xl border border-slate-700/80 shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-500 text-white shadow-lg shadow-blue-500/20 mb-1">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              {isRegister ? 'Create Your Account' : 'Welcome to SalesMind AI'}
            </h2>
            <p className="text-xs text-slate-400 max-w-xs mx-auto">
              {isRegister
                ? 'Join SalesMind AI to start generating predictive sales intelligence.'
                : 'Sign in to access your sales telemetry and forecasting models.'}
            </p>
          </div>

          {/* Auth Tab Switcher */}
          <div className="grid grid-cols-2 p-1 bg-slate-900/90 rounded-xl border border-slate-800 text-xs font-semibold">
            <button
              type="button"
              onClick={() => { setIsRegister(false); setErrorMsg(null) }}
              className={`py-2 rounded-lg transition ${
                !isRegister
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsRegister(true); setErrorMsg(null) }}
              className={`py-2 rounded-lg transition ${
                isRegister
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Create Account
            </button>
          </div>

          {errorMsg && (
            <div className="p-3 bg-danger/10 border border-danger/40 text-danger rounded-xl text-xs text-center font-medium leading-relaxed">
              {typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg)}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span>Corporate Email</span>
              </label>
              <input 
                type="email" 
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@enterprise.com"
                className="w-full bg-slate-900/90 text-white px-3.5 py-2.5 rounded-xl border border-slate-700 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition placeholder:text-slate-500"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-slate-400" />
                <span>Password</span>
              </label>
              <input 
                type="password" 
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-slate-900/90 text-white px-3.5 py-2.5 rounded-xl border border-slate-700 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary text-sm transition placeholder:text-slate-500"
              />
            </div>

            {isRegister && (
              <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1.5">
                <span className="font-semibold text-slate-300 block text-xs">Password Security Policy:</span>
                <ul className="space-y-1 text-[11px]">
                  <li className={`flex items-center gap-1.5 ${password.length >= 12 ? 'text-emerald-400' : 'text-slate-400'}`}>
                    <span>{password.length >= 12 ? '✓' : '•'}</span>
                    <span>At least 12 characters (current: {password.length})</span>
                  </li>
                  <li className={`flex items-center gap-1.5 ${/[A-Z]/.test(password) && /[a-z]/.test(password) ? 'text-emerald-400' : 'text-slate-400'}`}>
                    <span>{/[A-Z]/.test(password) && /[a-z]/.test(password) ? '✓' : '•'}</span>
                    <span>Both uppercase (A-Z) and lowercase (a-z) letters</span>
                  </li>
                  <li className={`flex items-center gap-1.5 ${/[0-9]/.test(password) ? 'text-emerald-400' : 'text-slate-400'}`}>
                    <span>{/[0-9]/.test(password) ? '✓' : '•'}</span>
                    <span>At least one numeric digit (0-9)</span>
                  </li>
                  <li className={`flex items-center gap-1.5 ${/[\W_]/.test(password) ? 'text-emerald-400' : 'text-slate-400'}`}>
                    <span>{/[\W_]/.test(password) ? '✓' : '•'}</span>
                    <span>At least one special character (!@#$%^&*)</span>
                  </li>
                </ul>
              </div>
            )}

            <button 
              type="submit"
              disabled={submitting}
              className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white py-3 rounded-xl font-bold text-sm shadow-lg shadow-blue-500/25 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {submitting ? (
                <span>Authenticating...</span>
              ) : isRegister ? (
                <>
                  <span>Create Account & Launch</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              ) : (
                <>
                  <span>Sign In to Dashboard</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="pt-2 text-center text-xs text-slate-400 border-t border-slate-800 flex items-center justify-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Protected by JWT & Bcrypt Ledger Authentication</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen w-screen items-center justify-center bg-background text-slate-400">
        <p className="text-sm">Loading SalesMind AI Portal...</p>
      </div>
    }>
      <LoginFormContent />
    </Suspense>
  )
}
