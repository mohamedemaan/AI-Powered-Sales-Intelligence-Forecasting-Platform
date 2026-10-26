'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '../../hooks/useAuth'

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { login, register, logout, user } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setSubmitting(true)

    const result = isRegister 
      ? await register(email, password)
      : await login(email, password)

    if (!result.success) {
      setErrorMsg(result.error || 'Authentication failed')
    }
    setSubmitting(false)
  }

  // If already logged in, show profile card
  if (user) {
    return (
      <div className="flex items-center justify-center min-h-[75vh]">
        <div className="bg-surface p-8 rounded-2xl border border-slate-700 w-full max-w-md shadow-2xl space-y-6 text-center">
          <div className="w-16 h-16 bg-primary/20 text-primary rounded-full flex items-center justify-center mx-auto text-2xl font-bold">
            {user.email.charAt(0).toUpperCase()}
          </div>
          
          <div>
            <h2 className="text-2xl font-bold text-white">Active Session</h2>
            <p className="text-sm text-slate-400 mt-1">{user.email}</p>
          </div>

          <div className="bg-background/80 p-4 rounded-xl border border-slate-700 text-left space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Role:</span>
              <span className="text-primary font-mono font-semibold">{user.role}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Status:</span>
              <span className="text-accent font-semibold">{user.is_active ? 'Active' : 'Inactive'}</span>
            </div>
            {user.tenant_id && (
              <div className="flex justify-between">
                <span className="text-slate-400">Tenant:</span>
                <span className="text-slate-300 font-mono">{user.tenant_id.slice(0, 8)}...</span>
              </div>
            )}
          </div>

          <div className="space-y-3 pt-2">
            <Link
              href="/"
              className="block w-full bg-primary text-white p-3 rounded-lg font-bold hover:bg-blue-600 transition"
            >
              Go to Dashboard
            </Link>
            <button
              onClick={logout}
              className="w-full bg-slate-800 text-slate-300 p-2.5 rounded-lg text-sm font-semibold hover:bg-slate-700 hover:text-white transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center min-h-[75vh]">
      <div className="bg-surface p-8 rounded-2xl border border-slate-700 w-full max-w-md shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-white">
            {isRegister ? 'Create Your SaaS Account' : 'Welcome to Sales Intel AI'}
          </h2>
          <p className="text-sm text-slate-400">
            {isRegister ? 'Register to manage models and demand forecasts' : 'Sign in to access your intelligence dashboard'}
          </p>
        </div>

        {errorMsg && (
          <div className="p-3 bg-danger/20 border border-danger/50 text-danger rounded-lg text-sm text-center">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Corporate Email</label>
            <input 
              type="email" 
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@enterprise.com"
              className="w-full bg-background text-white p-3 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm"
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 block mb-1">Password</label>
            <input 
              type="password" 
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full bg-background text-white p-3 rounded-lg border border-slate-600 focus:outline-none focus:border-primary text-sm"
            />
          </div>

          <button 
            type="submit"
            disabled={submitting}
            className="w-full bg-primary text-white p-3 rounded-lg font-bold hover:bg-blue-600 transition disabled:opacity-50"
          >
            {submitting ? 'Authenticating...' : isRegister ? 'Register Account' : 'Sign In'}
          </button>
        </form>

        <div className="text-center text-sm text-slate-400 pt-2 border-t border-slate-700/60">
          {isRegister ? (
            <p>
              Already have an account?{' '}
              <button 
                type="button" 
                onClick={() => { setIsRegister(false); setErrorMsg(null) }}
                className="text-primary hover:underline font-semibold"
              >
                Sign In
              </button>
            </p>
          ) : (
            <p>
              Don&apos;t have an account yet?{' '}
              <button 
                type="button" 
                onClick={() => { setIsRegister(true); setErrorMsg(null) }}
                className="text-primary hover:underline font-semibold"
              >
                Register
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
