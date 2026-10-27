'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import Link from 'next/link'
import api from '../../lib/api'
import {
  ShieldAlert,
  ShieldCheck,
  FileText,
  Filter,
  RefreshCw,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Info,
  Clock,
  User,
  Activity,
  X,
  Code
} from 'lucide-react'

interface AuditLogEntry {
  id: string
  tenant_id: string
  actor_id?: string | null
  actor_email?: string | null
  event_type: string
  target_type?: string | null
  target_id?: string | null
  outcome: string
  metadata_json?: Record<string, any> | null
  created_at: string
}

interface AuditLogResponse {
  items: AuditLogEntry[]
  total: number
  page: number
  limit: number
  total_pages: number
}

const EVENT_TYPE_OPTIONS = [
  { value: 'ALL', label: 'All Event Types' },
  { value: 'MEMBER_INVITED', label: 'Member Invited' },
  { value: 'INVITATION_ACCEPTED', label: 'Invitation Accepted' },
  { value: 'INVITATION_REVOKED', label: 'Invitation Revoked' },
  { value: 'MEMBER_ROLE_UPDATED', label: 'Role Updated' },
  { value: 'MEMBER_REMOVED', label: 'Member Removed' },
  { value: 'WORKSPACE_CREATED', label: 'Workspace Created' },
  { value: 'WORKSPACE_SETTINGS_UPDATED', label: 'Workspace Updated' },
  { value: 'DATASET_UPLOADED', label: 'Dataset Uploaded' },
  { value: 'DATASET_CLEANED', label: 'Dataset Cleaned' },
  { value: 'DATASET_RESET', label: 'Dataset Reset' },
  { value: 'FORECAST_GENERATED', label: 'Forecast Generated' },
  { value: 'PLAN_UPGRADED', label: 'Plan Upgraded' },
  { value: 'SUBSCRIPTION_CANCELED', label: 'Subscription Canceled' },
]

export default function AuditLogsPage() {
  const { user, activeOrg } = useAuth()
  const [logs, setLogs] = useState<AuditLogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(20)
  const [eventTypeFilter, setEventTypeFilter] = useState('ALL')
  const [outcomeFilter, setOutcomeFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null)

  const isAdminOrOwner = activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN'

  const fetchAuditLogs = async () => {
    if (!activeOrg?.id || !isAdminOrOwner) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setErrorMsg(null)
      const params: Record<string, any> = {
        page,
        limit,
      }
      if (eventTypeFilter !== 'ALL') params.event_type = eventTypeFilter
      if (outcomeFilter !== 'ALL') params.outcome = outcomeFilter

      const res = await api.get(`/api/v1/organizations/${activeOrg.id}/audit-logs`, { params })
      setLogs(res.data.items || [])
      setTotal(res.data.total || 0)
      setTotalPages(res.data.total_pages || 1)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load organization audit logs.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAuditLogs()
  }, [activeOrg?.id, page, limit, eventTypeFilter, outcomeFilter])

  const getEventBadge = (eventType: string) => {
    if (eventType.includes('MEMBER') || eventType.includes('INVITATION')) {
      return 'bg-purple-900/40 text-purple-300 border-purple-800/60'
    }
    if (eventType.includes('DATASET')) {
      return 'bg-blue-900/40 text-blue-300 border-blue-800/60'
    }
    if (eventType.includes('FORECAST')) {
      return 'bg-emerald-900/40 text-emerald-300 border-emerald-800/60'
    }
    if (eventType.includes('PLAN') || eventType.includes('SUBSCRIPTION')) {
      return 'bg-amber-900/40 text-amber-300 border-amber-800/60'
    }
    return 'bg-slate-800 text-slate-300 border-slate-700'
  }

  const formatTimestamp = (ts: string) => {
    try {
      const d = new Date(ts)
      return d.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return ts
    }
  }

  if (!isAdminOrOwner) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="pb-2 border-b border-slate-800">
          <h2 className="text-3xl font-bold tracking-tight text-white">Organization Audit Logs</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Security audit trail and operational event history.
          </p>
        </header>

        <div className="bg-surface p-8 rounded-xl border border-slate-700 shadow-sm text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-lg font-bold text-white">Administrator Access Required</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Organization audit logs provide an immutable trail of security, user role mutations, dataset actions, and billing events. Access is restricted to workspace <strong>Owners</strong> and <strong>Administrators</strong>.
            </p>
            <p className="text-xs text-slate-500 pt-2">
              Your current role in <span className="text-slate-300 font-medium">{activeOrg?.name || 'this workspace'}</span> is <span className="font-mono uppercase text-primary font-semibold">{activeOrg?.role || 'VIEWER'}</span>.
            </p>
          </div>
          <div className="pt-2">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 text-xs text-white px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition"
            >
              Return to Dashboard
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header className="pb-2 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Organization Audit Logs</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Immutable audit trail of security, mutations, and executions for <strong className="text-white">{activeOrg?.name}</strong>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchAuditLogs()}
            disabled={loading}
            className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </header>

      {/* Filter Toolbar */}
      <div className="bg-surface p-4 rounded-xl border border-slate-700/80 flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-semibold text-slate-300">Filter:</span>
          </div>

          {/* Event Type Select */}
          <select
            value={eventTypeFilter}
            onChange={(e) => {
              setEventTypeFilter(e.target.value)
              setPage(1)
            }}
            className="text-xs bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-primary"
          >
            {EVENT_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Outcome Select */}
          <select
            value={outcomeFilter}
            onChange={(e) => {
              setOutcomeFilter(e.target.value)
              setPage(1)
            }}
            className="text-xs bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-200 focus:outline-none focus:border-primary"
          >
            <option value="ALL">All Outcomes</option>
            <option value="SUCCESS">Success Only</option>
            <option value="FAILURE">Failure Only</option>
          </select>
        </div>

        <div className="text-xs text-slate-400">
          Showing <span className="text-white font-medium">{logs.length}</span> of <span className="text-white font-medium">{total}</span> total events
        </div>
      </div>

      {/* Error Message */}
      {errorMsg && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Audit Log Table */}
      <div className="bg-surface rounded-xl border border-slate-700/80 overflow-hidden shadow-sm">
        {loading && logs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
            <p className="text-sm">Querying immutable audit ledger...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <Activity className="w-8 h-8 text-slate-600 mx-auto" />
            <p className="text-sm font-medium text-slate-400">No audit events found</p>
            <p className="text-xs text-slate-500">
              No audit records match the current filter criteria for this workspace.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40 text-slate-400 uppercase tracking-wider font-semibold text-[11px]">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Target Resource</th>
                  <th className="py-3 px-4">Outcome</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    {/* Timestamp */}
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                      {formatTimestamp(log.created_at)}
                    </td>

                    {/* Event Type Badge */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase font-semibold border ${getEventBadge(
                          log.event_type
                        )}`}
                      >
                        {log.event_type}
                      </span>
                    </td>

                    {/* Actor */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        <span className="font-medium text-white truncate max-w-[180px]">
                          {log.actor_email || (log.actor_id ? log.actor_id.slice(0, 8) + '...' : 'System')}
                        </span>
                      </div>
                    </td>

                    {/* Target */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {log.target_type ? (
                        <span className="text-slate-300">
                          <strong className="text-slate-400 font-mono text-[10px]">{log.target_type}:</strong>{' '}
                          <span className="font-mono text-[11px] text-slate-300">
                            {log.target_id ? log.target_id.slice(0, 24) : 'N/A'}
                          </span>
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>

                    {/* Outcome */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                          log.outcome === 'SUCCESS'
                            ? 'bg-emerald-950/50 text-emerald-400 border border-emerald-800/50'
                            : 'bg-red-950/50 text-red-400 border border-red-800/50'
                        }`}
                      >
                        {log.outcome === 'SUCCESS' ? (
                          <ShieldCheck className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <ShieldAlert className="w-3 h-3 text-red-400" />
                        )}
                        {log.outcome}
                      </span>
                    </td>

                    {/* Inspect Metadata */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-white px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 rounded transition"
                      >
                        <Code className="w-3 h-3 text-primary" />
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <span>Items per page:</span>
              <select
                value={limit}
                onChange={(e) => {
                  setLimit(Number(e.target.value))
                  setPage(1)
                }}
                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>

            <div className="flex items-center gap-3">
              <span>
                Page <strong className="text-white">{page}</strong> of <strong className="text-white">{totalPages}</strong>
              </span>
              <div className="flex items-center gap-1">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="p-1.5 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 disabled:opacity-30 disabled:pointer-events-none transition"
                >
                  <ChevronLeft className="w-4 h-4 text-slate-300" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="p-1.5 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 disabled:opacity-30 disabled:pointer-events-none transition"
                >
                  <ChevronRight className="w-4 h-4 text-slate-300" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Metadata Inspector Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-surface border border-slate-700 rounded-xl max-w-lg w-full p-6 space-y-4 shadow-xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-primary" />
                <h3 className="font-bold text-white text-base">Audit Event Details</h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-semibold">Event Type</span>
                  <span className="text-slate-200 font-mono font-semibold">{selectedLog.event_type}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-semibold">Outcome</span>
                  <span className={selectedLog.outcome === 'SUCCESS' ? 'text-emerald-400 font-semibold' : 'text-red-400 font-semibold'}>
                    {selectedLog.outcome}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-semibold">Actor Email</span>
                  <span className="text-slate-200 font-medium">{selectedLog.actor_email || 'System'}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-semibold">Actor ID</span>
                  <span className="text-slate-400 font-mono text-[11px]">{selectedLog.actor_id || 'N/A'}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-500 block text-[10px] uppercase font-semibold">Timestamp</span>
                  <span className="text-slate-300 font-mono">{formatTimestamp(selectedLog.created_at)}</span>
                </div>
              </div>

              <div>
                <span className="text-slate-400 font-semibold block mb-1">Sanitized Metadata:</span>
                <pre className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-60 leading-relaxed">
                  {JSON.stringify(selectedLog.metadata_json || {}, null, 2)}
                </pre>
              </div>

              <div className="text-[11px] text-slate-500 flex items-center gap-1.5 pt-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                <span>All secret tokens, password hashes, and sensitive keys are automatically redacted.</span>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
