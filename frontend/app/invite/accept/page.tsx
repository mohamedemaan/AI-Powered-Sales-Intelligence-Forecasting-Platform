'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import api from '../../../lib/api'
import { useAuth } from '../../../hooks/useAuth'
import {
  Building2,
  ShieldCheck,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Loader2,
  Users
} from 'lucide-react'

interface InvitationDetails {
  organization_name: string
  organization_id: string
  email: string
  role: string
  status: string
  expires_at: string
  is_valid: boolean
  message?: string
}

function AcceptInviteContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')
  const { user, loading: authLoading } = useAuth()

  const [loading, setLoading] = useState(true)
  const [invite, setInvite] = useState<InvitationDetails | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setError('No invitation token provided in the URL.')
      setLoading(false)
      return
    }

    const verifyToken = async () => {
      try {
        setLoading(true)
        const res = await api.get(`/api/v1/organizations/invitations/verify?token=${encodeURIComponent(token)}`)
        setInvite(res.data)
      } catch (err: any) {
        const msg = err.response?.data?.detail || 'Failed to verify invitation token.'
        setError(msg)
      } finally {
        setLoading(false)
      }
    }

    verifyToken()
  }, [token])

  const handleAccept = async () => {
    if (!token) return
    try {
      setActionLoading(true)
      setError(null)
      const res = await api.post('/api/v1/organizations/invitations/accept', { token })
      setSuccessMsg(`Successfully joined ${res.data.name}! Switching workspace context...`)
      setTimeout(() => {
        window.location.href = '/'
      }, 1500)
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to accept invitation.'
      setError(msg)
      setActionLoading(false)
    }
  }

  const handleDecline = async () => {
    if (!token) return
    try {
      setActionLoading(true)
      setError(null)
      await api.post('/api/v1/organizations/invitations/reject', { token })
      setSuccessMsg('You have declined the invitation.')
      setTimeout(() => {
        router.push('/')
      }, 1500)
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to decline invitation.'
      setError(msg)
      setActionLoading(false)
    }
  }

  if (loading || authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-md w-full text-center space-y-4">
          <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto" />
          <h3 className="text-lg font-bold text-white">Validating Invitation</h3>
          <p className="text-xs text-slate-400">Verifying single-use cryptographic token security...</p>
        </div>
      </div>
    )
  }

  if (error || !invite || !invite.is_valid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
        <div className="bg-slate-900 border border-red-900/50 rounded-2xl p-8 max-w-md w-full text-center space-y-4 shadow-xl shadow-red-950/20">
          <div className="w-12 h-12 bg-red-900/30 border border-red-700/50 rounded-xl flex items-center justify-center text-red-400 mx-auto">
            <XCircle className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Invalid or Expired Invitation</h3>
          <p className="text-xs text-slate-400">
            {error || invite?.message || 'This invitation link is invalid, expired, or has already been used.'}
          </p>
          <div className="pt-2">
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white text-xs px-5 py-2.5 rounded-xl font-medium transition"
            >
              Return to Platform <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (successMsg) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
        <div className="bg-slate-900 border border-emerald-900/50 rounded-2xl p-8 max-w-md w-full text-center space-y-4 shadow-xl shadow-emerald-950/20">
          <div className="w-12 h-12 bg-emerald-900/30 border border-emerald-700/50 rounded-xl flex items-center justify-center text-emerald-400 mx-auto">
            <CheckCircle className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white">Invitation Accepted!</h3>
          <p className="text-xs text-emerald-400 font-medium">{successMsg}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 max-w-md w-full relative z-10 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 bg-primary/10 border border-primary/20 rounded-2xl flex items-center justify-center text-primary mx-auto shadow-inner">
            <Building2 className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-bold text-white">Join Workspace</h2>
          <p className="text-xs text-slate-400">
            You have been invited to collaborate on SalesMind AI.
          </p>
        </div>

        {/* Invite details card */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-slate-400">Workspace:</span>
            <span className="font-semibold text-white text-sm">{invite.organization_name}</span>
          </div>
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-slate-400">Assigned Role:</span>
            <span className="font-mono text-primary font-bold bg-primary/10 border border-primary/20 px-2 py-0.5 rounded text-[11px]">
              {invite.role}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Invited Email:</span>
            <span className="font-mono text-slate-300">{invite.email}</span>
          </div>
        </div>

        {/* Auth status check */}
        {!user ? (
          <div className="space-y-3">
            <div className="bg-amber-950/30 border border-amber-800/40 rounded-xl p-3 text-xs text-amber-300 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <span>Please log in or create an account to accept this workspace invitation.</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Link
                href={`/login?redirect=${encodeURIComponent(`/invite/accept?token=${token}`)}`}
                className="w-full text-center bg-primary hover:bg-blue-600 text-white text-xs font-semibold py-2.5 rounded-xl transition"
              >
                Log In
              </Link>
              <Link
                href={`/login?mode=register&email=${encodeURIComponent(invite.email)}&redirect=${encodeURIComponent(`/invite/accept?token=${token}`)}`}
                className="w-full text-center bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold py-2.5 rounded-xl border border-slate-700 transition"
              >
                Register
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-[11px] text-slate-400 text-center">
              Signed in as <strong className="text-white">{user.email}</strong>
            </p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={handleAccept}
                disabled={actionLoading}
                className="w-full inline-flex items-center justify-center gap-1.5 bg-primary hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-semibold py-2.5 rounded-xl transition shadow-lg shadow-blue-500/20"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                Accept & Join
              </button>
              <button
                onClick={handleDecline}
                disabled={actionLoading}
                className="w-full inline-flex items-center justify-center gap-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 hover:text-white text-xs font-semibold py-2.5 rounded-xl border border-slate-700 transition"
              >
                Decline
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AcceptInvitePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950 p-4">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
      }
    >
      <AcceptInviteContent />
    </Suspense>
  )
}
