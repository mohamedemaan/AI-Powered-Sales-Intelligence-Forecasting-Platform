'use client'

import { useAuth } from '../../hooks/useAuth'
import Link from 'next/link'
import {
  User,
  Shield,
  Building,
  Key,
  LogOut,
  CheckCircle,
  Database,
  ArrowRight,
  Lock
} from 'lucide-react'

export default function ProfilePage() {
  const { user, logout, loading } = useAuth()

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto p-12 text-center text-slate-500">
        <p className="animate-pulse">Loading user profile telemetry...</p>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto p-8 bg-surface rounded-2xl border border-slate-700 text-center space-y-4">
        <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary mx-auto">
          <Lock className="w-6 h-6" />
        </div>
        <h3 className="text-xl font-bold text-white">Sign In Required</h3>
        <p className="text-xs text-slate-400">
          You are currently accessing the platform as an unauthenticated session. Please sign in or register to manage your tenant workspace and settings.
        </p>
        <Link
          href="/login"
          className="inline-flex items-center gap-2 bg-primary text-white text-xs px-5 py-2.5 rounded-xl font-medium hover:bg-blue-600 transition"
        >
          Sign In / Create Account <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <header className="pb-2 border-b border-slate-800">
        <h2 className="text-3xl font-bold tracking-tight text-white">User Profile & Tenant Workspace</h2>
        <p className="text-slate-400 text-sm mt-0.5">
          Account identity, RBAC authorization privileges, and multi-tenant isolation settings.
        </p>
      </header>

      {/* Account Identity Card */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <User className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">{user.email}</h3>
              <span className="text-xs text-slate-400">Platform Account Identity</span>
            </div>
          </div>
          <span className="text-xs bg-primary/20 text-primary border border-primary/30 px-3 py-1 rounded-full font-mono font-semibold uppercase">
            {user.role}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-800 text-xs">
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">User UUID</span>
            <span className="font-mono text-slate-200 truncate block mt-0.5" title={user.id}>
              {user.id}
            </span>
          </div>

          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Account Status</span>
            <span className="inline-flex items-center gap-1.5 text-emerald-400 font-semibold mt-0.5">
              <CheckCircle className="w-3.5 h-3.5" /> Active & Verified
            </span>
          </div>

          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Assigned Role</span>
            <span className="text-slate-200 font-medium mt-0.5 block">
              {user.role === 'ADMIN' ? 'Full Administrator' : 'Sales & Forecast Analyst'}
            </span>
          </div>
        </div>
      </div>

      {/* Workspace & Multi-Tenant Isolation */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Building className="w-5 h-5 text-primary" />
          <h3 className="text-base font-semibold text-white">Multi-Tenant Isolation & Workspace Scope</h3>
        </div>

        <p className="text-xs text-slate-300">
          The Sales Intelligence Platform enforces strict tenant-level row isolation. Data ingestion, sales transactions, model runs, and generated reports belong exclusively to your organization's workspace partition.
        </p>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Workspace Tenant ID:</span>
            <span className="font-mono font-medium text-white">
              {user.tenant_id || 'Global Enterprise Sandbox (Tenant-01)'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Data Access Policy:</span>
            <span className="text-emerald-400 font-medium">Tenant Isolated (Strict Scoping)</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">API Authentication:</span>
            <span className="text-slate-200 font-mono">Bearer JWT (HS256)</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <Link
            href="/data"
            className="inline-flex items-center gap-1.5 text-xs bg-slate-800 text-slate-300 hover:text-white px-3 py-2 rounded-lg border border-slate-700 transition"
          >
            <Database className="w-3.5 h-3.5 text-primary" /> Ingested Datasets
          </Link>
          <Link
            href="/reports"
            className="inline-flex items-center gap-1.5 text-xs bg-slate-800 text-slate-300 hover:text-white px-3 py-2 rounded-lg border border-slate-700 transition"
          >
            Audited Reports & Exports
          </Link>
        </div>
      </div>

      {/* Security Policies & Password Hygiene */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-semibold text-white">Security & Password Standards</h3>
        </div>

        <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-5">
          <li>Passwords must meet enterprise complexity rules (12+ characters, uppercase, lowercase, number, symbol).</li>
          <li>All stored credentials hashed using bcrypt with salt rounds.</li>
          <li>JWT tokens expire automatically after 8 days of inactivity.</li>
        </ul>

        <div className="pt-2">
          <button
            onClick={logout}
            className="inline-flex items-center gap-2 bg-danger/15 hover:bg-danger/25 text-danger border border-danger/30 text-xs font-semibold px-4 py-2 rounded-lg transition"
          >
            <LogOut className="w-3.5 h-3.5" /> Terminate Active Session (Sign Out)
          </button>
        </div>
      </div>
    </div>
  )
}

