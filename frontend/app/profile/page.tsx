'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import Link from 'next/link'
import api from '../../lib/api'
import {
  User,
  Shield,
  Building,
  Key,
  LogOut,
  CreditCard,
  CheckCircle,
  Database,
  ArrowRight,
  Lock,
  Users,
  UserPlus,
  Mail,
  Copy,
  Trash2,
  AlertCircle,
  Clock,
  ShieldAlert,
  ShieldCheck,
  Loader2,
  Check
} from 'lucide-react'

interface Member {
  id: string
  tenant_id: string
  user_id: string
  role: string
  email?: string
  username?: string
  full_name?: string
  created_at: string
}

interface Invitation {
  id: string
  tenant_id: string
  email: string
  role: string
  status: string
  expires_at: string
  created_at: string
  invited_by_name?: string
  invitation_link?: string
  development_mode_note?: string
}

export default function ProfilePage() {
  const { user, logout, loading, activeOrg, organizations } = useAuth()

  // Team Management state
  const [members, setMembers] = useState<Member[]>([])
  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [loadingTeam, setLoadingTeam] = useState(false)
  const [teamError, setTeamError] = useState<string | null>(null)
  const [teamSuccess, setTeamSuccess] = useState<string | null>(null)

  // Invite Form modal state
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('ANALYST')
  const [inviting, setInviting] = useState(false)
  const [generatedInviteLink, setGeneratedInviteLink] = useState<string | null>(null)
  const [copiedLink, setCopiedLink] = useState(false)

  // Member action state
  const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null)

  const isOrgAdmin = activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN'

  useEffect(() => {
    if (!activeOrg?.id || !user) return

    const loadTeamData = async () => {
      try {
        setLoadingTeam(true)
        setTeamError(null)
        // 1. Fetch Members
        const memRes = await api.get(`/api/v1/organizations/${activeOrg.id}/members`)
        setMembers(memRes.data)

        // 2. Fetch Invitations (if admin)
        if (isOrgAdmin) {
          try {
            const invRes = await api.get(`/api/v1/organizations/${activeOrg.id}/invitations`)
            setInvitations(invRes.data)
          } catch (e) {
            // Ignored if user not authorized
          }
        }
      } catch (err: any) {
        console.error('Failed to load team:', err)
      } finally {
        setLoadingTeam(false)
      }
    }

    loadTeamData()
  }, [activeOrg?.id, activeOrg?.role, user])

  const handleCreateInvite = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeOrg?.id || !inviteEmail.trim()) return

    try {
      setInviting(true)
      setTeamError(null)
      const res = await api.post(`/api/v1/organizations/${activeOrg.id}/invitations`, {
        email: inviteEmail.trim(),
        role: inviteRole
      })

      const fullLink = `${window.location.origin}${res.data.invitation_link}`
      setGeneratedInviteLink(fullLink)
      setInvitations([res.data, ...invitations])
      setTeamSuccess(`Invitation issued for ${inviteEmail.trim()}`)
      setInviteEmail('')
    } catch (err: any) {
      setTeamError(err.response?.data?.detail || 'Failed to issue invitation.')
    } finally {
      setInviting(false)
    }
  }

  const handleRevokeInvite = async (invId: string) => {
    if (!activeOrg?.id) return
    if (!confirm('Are you sure you want to revoke this invitation?')) return

    try {
      await api.delete(`/api/v1/organizations/${activeOrg.id}/invitations/${invId}`)
      setInvitations(invitations.map(inv => inv.id === invId ? { ...inv, status: 'REVOKED' } : inv))
      setTeamSuccess('Invitation revoked successfully.')
    } catch (err: any) {
      setTeamError(err.response?.data?.detail || 'Failed to revoke invitation.')
    }
  }

  const handleUpdateRole = async (targetUserId: string, newRole: string) => {
    if (!activeOrg?.id) return

    try {
      setUpdatingMemberId(targetUserId)
      setTeamError(null)
      const res = await api.patch(`/api/v1/organizations/${activeOrg.id}/members/${targetUserId}`, {
        role: newRole
      })
      setMembers(members.map(m => m.user_id === targetUserId ? { ...m, role: res.data.role } : m))
      setTeamSuccess(`Role updated to ${newRole}`)
    } catch (err: any) {
      setTeamError(err.response?.data?.detail || 'Failed to update member role.')
    } finally {
      setUpdatingMemberId(null)
    }
  }

  const handleRemoveMember = async (targetUserId: string, targetEmail?: string) => {
    if (!activeOrg?.id) return
    if (!confirm(`Are you sure you want to remove ${targetEmail || 'this member'} from the workspace?`)) return

    try {
      setUpdatingMemberId(targetUserId)
      setTeamError(null)
      await api.delete(`/api/v1/organizations/${activeOrg.id}/members/${targetUserId}`)
      setMembers(members.filter(m => m.user_id !== targetUserId))
      setTeamSuccess('Member removed from workspace.')
    } catch (err: any) {
      setTeamError(err.response?.data?.detail || 'Failed to remove member.')
    } finally {
      setUpdatingMemberId(null)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedLink(true)
    setTimeout(() => setCopiedLink(false), 2500)
  }

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
    <div className="max-w-5xl mx-auto space-y-6">
      <header className="pb-2 border-b border-slate-800">
        <h2 className="text-3xl font-bold tracking-tight text-white">Account & Organization Workspace</h2>
        <p className="text-slate-400 text-sm mt-0.5">
          Workspace administration, team collaboration, secure role-based access control (RBAC), and multi-tenant telemetry.
        </p>
      </header>

      {/* Notifications */}
      {teamError && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{teamError}</span>
          </div>
          <button onClick={() => setTeamError(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {teamSuccess && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{teamSuccess}</span>
          </div>
          <button onClick={() => setTeamSuccess(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Account Identity Card */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <User className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">{user.email}</h3>
              <span className="text-xs text-slate-400">Authenticated Platform Identity</span>
            </div>
          </div>
          <span className="text-xs bg-primary/20 text-primary border border-primary/30 px-3 py-1 rounded-full font-mono font-semibold uppercase">
            {activeOrg?.role || user.role}
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
            <span className="text-slate-400 block text-[11px]">Active Workspace</span>
            <span className="text-white font-semibold block mt-0.5 truncate">
              {activeOrg?.name || 'Primary Workspace'}
            </span>
          </div>

          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Workspace Role</span>
            <span className="text-primary font-bold block mt-0.5">
              {activeOrg?.role || 'OWNER'}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 pt-2">
          <Link
            href="/billing"
            className="inline-flex items-center gap-1.5 text-xs text-white px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition"
          >
            <CreditCard className="w-3.5 h-3.5 text-primary" />
            Subscription & Usage Telemetry
          </Link>
          {(activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN') && (
            <Link
              href="/audit"
              className="inline-flex items-center gap-1.5 text-xs text-white px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Organization Audit Logs
            </Link>
          )}
        </div>
      </div>

      {/* Team Members & Collaboration Section */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-primary" />
              <h3 className="text-base font-semibold text-white">Team Members & Permissions</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Manage member roles, permissions, and workspace access for <strong className="text-white">{activeOrg?.name}</strong>.
            </p>
          </div>

          {isOrgAdmin && (
            <button
              onClick={() => {
                setShowInviteModal(true)
                setGeneratedInviteLink(null)
              }}
              className="inline-flex items-center gap-1.5 bg-primary hover:bg-blue-600 text-white text-xs font-semibold px-3.5 py-2 rounded-xl transition shadow-lg shadow-blue-500/10 self-start sm:self-auto"
            >
              <UserPlus className="w-4 h-4" /> Invite Team Member
            </button>
          )}
        </div>

        {/* Member List */}
        <div className="space-y-3">
          {loadingTeam ? (
            <div className="p-8 text-center text-xs text-slate-500">
              <Loader2 className="w-5 h-5 animate-spin mx-auto text-primary mb-2" />
              Loading organization members...
            </div>
          ) : members.length === 0 ? (
            <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-xl text-center text-xs text-slate-400">
              No members found in this workspace.
            </div>
          ) : (
            <div className="divide-y divide-slate-800 border border-slate-800 rounded-xl overflow-hidden bg-slate-900/40">
              {members.map((member) => {
                const isCurrentUser = member.user_id === user.id
                const isOwner = member.role === 'OWNER'

                return (
                  <div key={member.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-800/40 transition">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-slate-300 text-sm">
                        {member.full_name ? member.full_name.charAt(0).toUpperCase() : member.email?.charAt(0).toUpperCase() || 'U'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-semibold text-white">
                            {member.full_name || member.username || member.email}
                          </span>
                          {isCurrentUser && (
                            <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700">
                              You
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-slate-400 block font-mono">{member.email}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 self-end sm:self-auto">
                      {isOrgAdmin ? (
                        <select
                          value={member.role}
                          disabled={updatingMemberId === member.user_id || (!isCurrentUser && isOwner && activeOrg?.role !== 'OWNER')}
                          onChange={(e) => handleUpdateRole(member.user_id, e.target.value)}
                          className="bg-slate-950 border border-slate-700 text-slate-200 text-xs px-2.5 py-1.5 rounded-lg focus:outline-none focus:border-primary disabled:opacity-50"
                        >
                          <option value="OWNER">OWNER</option>
                          <option value="ADMIN">ADMIN</option>
                          <option value="ANALYST">ANALYST</option>
                          <option value="VIEWER">VIEWER</option>
                          <option value="MEMBER">MEMBER</option>
                        </select>
                      ) : (
                        <span className="text-xs bg-slate-800 text-slate-300 border border-slate-700 px-2.5 py-1 rounded-lg font-mono font-semibold">
                          {member.role}
                        </span>
                      )}

                      {isOrgAdmin && !isCurrentUser && (
                        <button
                          onClick={() => handleRemoveMember(member.user_id, member.email)}
                          disabled={updatingMemberId === member.user_id}
                          className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-950/30 rounded-lg transition disabled:opacity-50"
                          title="Remove member"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Invitations Table (Admins only) */}
        {isOrgAdmin && invitations.length > 0 && (
          <div className="pt-4 space-y-3">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-amber-400" /> Workspace Invitations ({invitations.length})
            </h4>

            <div className="divide-y divide-slate-800 border border-slate-800 rounded-xl overflow-hidden bg-slate-900/40 text-xs">
              {invitations.map((inv) => {
                const isPending = inv.status === 'PENDING'

                return (
                  <div key={inv.id} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-800/30 transition">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">{inv.email}</span>
                        <span className="text-[10px] font-mono bg-primary/10 text-primary border border-primary/20 px-1.5 py-0.5 rounded">
                          {inv.role}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        Expires: {new Date(inv.expires_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-auto">
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded-full font-semibold uppercase ${
                          inv.status === 'ACCEPTED'
                            ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/60'
                            : inv.status === 'PENDING'
                            ? 'bg-amber-950/60 text-amber-400 border border-amber-800/60'
                            : 'bg-slate-800 text-slate-400 border border-slate-700'
                        }`}
                      >
                        {inv.status}
                      </span>

                      {isPending && (
                        <button
                          onClick={() => handleRevokeInvite(inv.id)}
                          className="text-[11px] text-red-400 hover:text-red-300 px-2 py-1 bg-red-950/30 hover:bg-red-950/50 rounded-lg border border-red-900/50 transition"
                        >
                          Revoke
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl relative">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-primary" />
                <h3 className="text-base font-bold text-white">Invite Team Member</h3>
              </div>
              <button
                onClick={() => {
                  setShowInviteModal(false)
                  setGeneratedInviteLink(null)
                }}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {generatedInviteLink ? (
              <div className="space-y-4 py-2">
                <div className="p-3 bg-emerald-950/40 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Invitation created! Share this secure single-use link with the invitee:</span>
                </div>

                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                  <span className="text-[11px] text-slate-400 block">Invitation URL:</span>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value={generatedInviteLink}
                      className="bg-slate-900 border border-slate-800 text-xs font-mono text-slate-200 px-3 py-2 rounded-lg w-full truncate focus:outline-none"
                    />
                    <button
                      onClick={() => copyToClipboard(generatedInviteLink)}
                      className="inline-flex items-center gap-1.5 bg-primary hover:bg-blue-600 text-white text-xs px-3 py-2 rounded-lg font-semibold transition shrink-0"
                    >
                      {copiedLink ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedLink ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>

                <div className="p-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-[11px] text-slate-400">
                  <strong className="text-slate-300">Note:</strong> External SMTP delivery is disabled in development mode. The invitee can open the link above to accept.
                </div>

                <button
                  onClick={() => {
                    setShowInviteModal(false)
                    setGeneratedInviteLink(null)
                  }}
                  className="w-full bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold py-2.5 rounded-xl transition"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleCreateInvite} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300">Corporate Email</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
                    <input
                      type="email"
                      required
                      placeholder="colleague@company.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 pl-9 pr-3 py-2.5 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-300">Assigned Role</label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 px-3 py-2.5 rounded-xl text-xs text-white focus:outline-none focus:border-primary"
                  >
                    <option value="ADMIN">ADMIN — Manage team members & workspace settings</option>
                    <option value="ANALYST">ANALYST — Upload datasets, train models, run forecasts</option>
                    <option value="VIEWER">VIEWER — Read-only access to dashboards and reports</option>
                    <option value="MEMBER">MEMBER — Basic workspace collaborator</option>
                  </select>
                </div>

                <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-[11px] text-slate-400 flex items-start gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <span>
                    Generates a cryptographically secure, expiring token valid for 7 days.
                  </span>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowInviteModal(false)}
                    className="px-4 py-2 text-xs text-slate-400 hover:text-white transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={inviting || !inviteEmail.trim()}
                    className="inline-flex items-center gap-1.5 bg-primary hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-xl transition shadow-lg shadow-blue-500/20"
                  >
                    {inviting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <UserPlus className="w-3.5 h-3.5" />}
                    Issue Invitation
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

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
            <span className="text-slate-400">Active Workspace Name:</span>
            <span className="font-semibold text-white">
              {activeOrg?.name || 'Primary Workspace'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Workspace Member Role:</span>
            <span className="font-mono text-primary font-semibold">
              {activeOrg?.role || 'OWNER'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Subscription Tier:</span>
            <span className="font-mono text-slate-200">
              {activeOrg?.subscription_tier || 'FREE'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Workspace Tenant ID:</span>
            <span className="font-mono font-medium text-white">
              {activeOrg?.id || user.tenant_id || 'Global Enterprise Sandbox (Tenant-01)'}
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
          <Link
            href="/billing"
            className="inline-flex items-center gap-1.5 text-xs bg-primary/20 text-primary border border-primary/30 hover:bg-primary/30 px-3 py-2 rounded-lg font-semibold transition"
          >
            <CreditCard className="w-3.5 h-3.5" /> Manage Subscription & Quotas
          </Link>
        </div>
      </div>

      {/* Roles & Permissions Matrix (RBAC) */}
      <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <h3 className="text-base font-semibold text-white">Roles & Permissions Matrix</h3>
        </div>
        <p className="text-xs text-slate-300">
          Centralized Role-Based Access Control (RBAC) securely governs platform capabilities across your organization:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white">Owner</span>
              <span className="text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded font-semibold">FULL ACCESS</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Full organization control, workspace metadata settings, member role administration, billing configuration, and permanent workspace deletion.
            </p>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white">Admin</span>
              <span className="text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded font-semibold">ADMINISTRATION</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Invite and remove team members, update workspace metadata, manage datasets and deduplication, and audit telemetry. Cannot delete workspace or remove Owner.
            </p>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white">Analyst</span>
              <span className="text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded font-semibold">DATA & ML</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Upload datasets, execute ETL processing, trigger machine learning model training, run forecasts, and download audited reports. Cannot manage team members.
            </p>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white">Viewer</span>
              <span className="text-[10px] font-mono bg-slate-700/50 text-slate-300 border border-slate-600 px-2 py-0.5 rounded font-semibold">READ-ONLY</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Read-only view of dashboards, sales trends, inventory telemetry, and generated forecast charts. Strictly prevented from uploading data or modifying settings.
            </p>
          </div>
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
