'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '../../hooks/useAuth'
import {
  Building2,
  ChevronDown,
  Check,
  Plus,
  Loader2,
  X,
  Layers,
  ShieldCheck,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Overview' },
  { href: '/data', label: 'Data Ingestion & Preview' },
  { href: '/cleaning', label: 'Data Cleaning Studio' },
  { href: '/analytics', label: 'Sales Analytics' },
  { href: '/forecast', label: 'Forecast Lab' },
  { href: '/anomalies', label: 'Anomalies' },
  { href: '/scenarios', label: 'Scenario Lab' },
  { href: '/inventory', label: 'Inventory Intelligence' },
  { href: '/model-health', label: 'Model Health' },
  { href: '/gemini', label: 'Gemini AI' },
  { href: '/knowledge', label: 'Knowledge Base (RAG)' },
  { href: '/reports', label: 'Reports & Exports' },
  { href: '/billing', label: 'Subscription & Plans' },
  { href: '/audit', label: 'Audit Logs' },
]

export function Sidebar() {
  const pathname = usePathname()
  const { user, logout, organizations, activeOrg, switchOrganization, createOrganization } = useAuth()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [newOrgName, setNewOrgName] = useState('')
  const [newOrgSlug, setNewOrgSlug] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [isSwitching, setIsSwitching] = useState<string | null>(null)
  const [createError, setCreateError] = useState<string | null>(null)

  const handleSwitch = async (orgId: string) => {
    if (orgId === activeOrg?.id) {
      setDropdownOpen(false)
      return
    }
    setIsSwitching(orgId)
    await switchOrganization(orgId)
    setIsSwitching(null)
    setDropdownOpen(false)
  }

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newOrgName.trim()) return

    setIsCreating(true)
    setCreateError(null)

    const res = await createOrganization(newOrgName.trim(), newOrgSlug.trim() || undefined)
    setIsCreating(false)

    if (res.success) {
      setNewOrgName('')
      setNewOrgSlug('')
      setModalOpen(false)
      setDropdownOpen(false)
    } else {
      setCreateError(res.error || 'Failed to create workspace.')
    }
  }

  return (
    <aside className="w-64 bg-surface border-r border-slate-700 flex flex-col p-4 relative select-none">
      {/* Brand Header */}
      <div className="mb-4">
        <h1 className="text-xl font-bold text-white tracking-tight">
          SalesMind <span className="text-primary">AI</span>
        </h1>
        <span className="text-xs text-primary font-mono block">Enterprise Platform</span>
      </div>

      {/* Multi-Tenant Workspace Selector */}
      {user && (
        <div className="relative mb-6">
          <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5 block">
            Workspace
          </label>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-800/90 hover:bg-slate-800 border border-slate-700 text-left transition group"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-6 h-6 rounded bg-primary/20 text-primary flex items-center justify-center shrink-0">
                <Building2 className="w-3.5 h-3.5" />
              </div>
              <div className="min-w-0 truncate">
                <p className="text-xs font-semibold text-white truncate group-hover:text-primary transition-colors">
                  {activeOrg?.name || 'Primary Workspace'}
                </p>
                <span className="text-[10px] text-slate-400 font-mono block">
                  {activeOrg?.role || 'OWNER'} • {activeOrg?.subscription_tier || 'FREE'}
                </span>
              </div>
            </div>
            <ChevronDown
              className={`w-3.5 h-3.5 text-slate-400 shrink-0 ml-1 transition-transform duration-200 ${
                dropdownOpen ? 'rotate-180 text-primary' : ''
              }`}
            />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1.5 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150">
              <div className="px-2 py-1 text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                Your Workspaces ({organizations.length})
              </div>

              <div className="max-h-48 overflow-y-auto space-y-1 my-1">
                {organizations.map((org) => {
                  const isActive = org.id === activeOrg?.id
                  return (
                    <button
                      key={org.id}
                      onClick={() => handleSwitch(org.id)}
                      disabled={isSwitching !== null}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-xs transition text-left ${
                        isActive
                          ? 'bg-primary/20 text-white font-medium'
                          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      <div className="min-w-0 truncate pr-2">
                        <span className="truncate block">{org.name}</span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {org.role} • {org.members_count} {org.members_count === 1 ? 'member' : 'members'}
                        </span>
                      </div>
                      {isSwitching === org.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-primary shrink-0" />
                      ) : isActive ? (
                        <Check className="w-3.5 h-3.5 text-primary shrink-0" />
                      ) : null}
                    </button>
                  )
                })}
              </div>

              <div className="pt-1.5 border-t border-slate-800">
                <button
                  onClick={() => {
                    setDropdownOpen(false)
                    setModalOpen(true)
                  }}
                  className="w-full flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-semibold text-primary hover:bg-primary/10 transition"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Create New Workspace
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Navigation Links */}
      <nav className="flex flex-col gap-3 text-sm font-medium overflow-y-auto pr-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href === '/gemini' && pathname === '/copilot')
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`hover:text-primary transition-colors py-1 ${
                isActive ? 'text-primary font-semibold' : 'text-slate-300'
              }`}
            >
              {item.label}
            </Link>
          )
        })}
      </nav>

      {/* User Session Footer */}
      <div className="mt-auto pt-4 border-t border-slate-700/60">
        {user ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Link
                href="/profile"
                className="text-xs text-slate-300 truncate font-medium hover:text-primary transition"
                title={user.email}
              >
                {user.email}
              </Link>
              <span className="text-[10px] bg-primary/20 text-primary px-1.5 py-0.5 rounded font-mono">
                {user.role}
              </span>
            </div>
            <div className="flex gap-2">
              <Link
                href="/profile"
                className="flex-1 text-center text-xs font-medium py-1 px-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
              >
                Profile & Workspace
              </Link>
              <button
                onClick={logout}
                className="text-center text-xs font-medium py-1 px-2 rounded-lg bg-slate-800 text-slate-400 hover:text-rose-400 hover:bg-slate-750 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        ) : (
          <Link
            href="/login"
            className="block text-center text-xs font-semibold py-2 px-3 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition"
          >
            Account / Sign In
          </Link>
        )}
      </div>

      {/* Create Organization Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-primary/20 text-primary flex items-center justify-center">
                  <Building2 className="w-4 h-4" />
                </div>
                <h3 className="text-base font-bold text-white">Create Company Workspace</h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Company workspaces provide dedicated multi-tenant isolation for your transaction datasets, ML forecasts, and team analytics.
            </p>

            {createError && (
              <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateOrg} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Workspace / Organization Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corp Retail"
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Workspace Identifier / Slug <span className="text-slate-500 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. acme-retail"
                  value={newOrgSlug}
                  onChange={(e) => setNewOrgSlug(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary transition"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-750 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating || !newOrgName.trim()}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold text-white bg-primary hover:bg-primary/90 transition disabled:opacity-50"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Workspace'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  )
}
