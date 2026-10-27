'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '../../hooks/useAuth'
import Link from 'next/link'
import api from '../../lib/api'
import {
  CreditCard,
  CheckCircle,
  AlertTriangle,
  Zap,
  Users,
  Database,
  TrendingUp,
  ShieldCheck,
  ArrowRight,
  Loader2,
  Check,
  Building,
  HardDrive,
  BarChart3,
  Calendar
} from 'lucide-react'

interface PlanInfo {
  tier: string
  name: string
  description: string
  price_monthly: number
  max_members: number
  max_datasets: number
  max_forecasts_per_month: number
  features: string[]
}

interface DetailedUsage {
  tenant_id: string
  tier: string
  plan_name: string
  datasets_count: number
  dataset_records_count: number
  estimated_storage_kb: number
  estimated_storage_mb: number
  forecasts_total_count: number
  forecasts_month_count: number
  forecasts_month_limit: number
  active_members_count: number
  total_seats_used: number
  seats_limit: number
  billing_cycle_start: string
}

interface SubscriptionDetails {
  tier: string
  name: string
  status: string
  current_period_end?: string
  usage: {
    members_count: number
    members_limit: number
    datasets_count: number
    datasets_limit: number
    forecasts_count_month: number
    forecasts_limit_month: number
    remaining_forecasts: number
    remaining_seats: number
  }
  available_plans: PlanInfo[]
  development_mode_note?: string
}

export default function BillingPage() {
  const { user, activeOrg } = useAuth()
  const [subDetails, setSubDetails] = useState<SubscriptionDetails | null>(null)
  const [detailedUsage, setDetailedUsage] = useState<DetailedUsage | null>(null)
  const [loading, setLoading] = useState(true)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [upgradingTier, setUpgradingTier] = useState<string | null>(null)

  const isOwner = activeOrg?.role === 'OWNER'

  const fetchSubscription = async () => {
    if (!activeOrg?.id) return
    try {
      setLoading(true)
      setErrorMsg(null)
      const [subRes, usageRes] = await Promise.all([
        api.get(`/api/v1/organizations/${activeOrg.id}/subscription`),
        api.get(`/api/v1/organizations/${activeOrg.id}/usage`).catch(() => null)
      ])
      setSubDetails(subRes.data)
      if (usageRes?.data) {
        setDetailedUsage(usageRes.data)
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load subscription details.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSubscription()
  }, [activeOrg?.id])

  const handleUpgrade = async (targetTier: string) => {
    if (!activeOrg?.id || !isOwner) return
    if (!confirm(`Confirm upgrade of ${activeOrg.name} to the ${targetTier} plan?`)) return

    try {
      setUpgradingTier(targetTier)
      setErrorMsg(null)
      const res = await api.post(`/api/v1/organizations/${activeOrg.id}/subscription/upgrade`, {
        plan_tier: targetTier
      })
      setSubDetails(res.data)
      setSuccessMsg(`Successfully upgraded to ${targetTier} plan! Quotas have been expanded.`)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upgrade plan.')
    } finally {
      setUpgradingTier(null)
    }
  }

  const handleCancel = async () => {
    if (!activeOrg?.id || !isOwner) return
    if (!confirm('Are you sure you want to schedule cancellation of this subscription?')) return

    try {
      setLoading(true)
      setErrorMsg(null)
      await api.post(`/api/v1/organizations/${activeOrg.id}/subscription/cancel`)
      setSuccessMsg('Subscription scheduled for cancellation at the end of the billing period.')
      fetchSubscription()
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to cancel subscription.')
      setLoading(false)
    }
  }

  if (loading && !subDetails) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center text-slate-500">
        <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto mb-3" />
        <p className="text-sm">Loading workspace billing telemetry...</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <header className="pb-2 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Subscription & Usage Limits</h2>
          <p className="text-slate-400 text-sm mt-0.5">
            Manage SaaS subscription tier, plan limits, and real-time usage metrics for <strong className="text-white">{activeOrg?.name}</strong>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/profile"
            className="text-xs text-slate-400 hover:text-white px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg transition"
          >
            &larr; Account Profile
          </Link>
        </div>
      </header>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 rounded-xl text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-slate-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Active Subscription Summary Card */}
      {subDetails && (
        <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                <CreditCard className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">{subDetails.name}</h3>
                  <span className="text-[10px] font-mono uppercase bg-primary/20 text-primary border border-primary/30 px-2 py-0.5 rounded-full font-semibold">
                    {subDetails.status}
                  </span>
                </div>
                <span className="text-xs text-slate-400">
                  {subDetails.current_period_end ? `Current period ends ${subDetails.current_period_end}` : 'Ongoing active billing cycle'}
                </span>
              </div>
            </div>

            {isOwner && subDetails.tier !== 'FREE' && subDetails.status !== 'CANCELED' && (
              <button
                onClick={handleCancel}
                className="text-xs text-red-400 hover:text-red-300 px-3 py-1.5 bg-red-950/30 hover:bg-red-950/50 border border-red-900/50 rounded-lg transition self-start sm:self-auto"
              >
                Cancel Subscription
              </button>
            )}
          </div>

          {/* Real-time Usage & Quota Progress Bars */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Team Members */}
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-primary" /> Team Seats
                </span>
                <span className="font-bold text-white">
                  {subDetails.usage.members_count} / {subDetails.usage.members_limit}
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-primary h-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, (subDetails.usage.members_count / subDetails.usage.members_limit) * 100)}%`
                  }}
                />
              </div>
              <span className="text-[10px] text-slate-500 block">
                {subDetails.usage.remaining_seats} seat(s) remaining
              </span>
            </div>

            {/* Monthly Forecast Runs */}
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Forecasts (Month)
                </span>
                <span className="font-bold text-white">
                  {subDetails.usage.forecasts_count_month} / {subDetails.usage.forecasts_limit_month}
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, (subDetails.usage.forecasts_count_month / subDetails.usage.forecasts_limit_month) * 100)}%`
                  }}
                />
              </div>
              <span className="text-[10px] text-slate-500 block">
                {subDetails.usage.remaining_forecasts} forecast runs remaining this month
              </span>
            </div>

            {/* Ingested Datasets */}
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-amber-400" /> Datasets Stored
                </span>
                <span className="font-bold text-white">
                  {subDetails.usage.datasets_count} / {subDetails.usage.datasets_limit}
                </span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-amber-500 h-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, (subDetails.usage.datasets_count / subDetails.usage.datasets_limit) * 100)}%`
                  }}
                />
              </div>
              <span className="text-[10px] text-slate-500 block">
                {subDetails.usage.datasets_limit - subDetails.usage.datasets_count} dataset slot(s) available
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Verified Resource Footprint & Storage Breakdown */}
      {detailedUsage && (
        <div className="bg-surface p-6 rounded-xl border border-slate-700 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-primary" />
              <h3 className="text-base font-semibold text-white">Verified Resource Footprint & Telemetry</h3>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Cycle Reset: <span className="text-slate-300 font-medium">{detailedUsage.billing_cycle_start}</span>
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px]">Database Records</span>
              <span className="text-xl font-bold text-white block">
                {detailedUsage.dataset_records_count.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-500 block">
                Ingested sales line items
              </span>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px]">Storage Footprint</span>
              <span className="text-xl font-bold text-white block">
                {detailedUsage.estimated_storage_mb.toFixed(2)} MB
              </span>
              <span className="text-[10px] text-slate-500 block">
                {detailedUsage.estimated_storage_kb.toFixed(1)} KB calculated indexing
              </span>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px]">Lifetime ML Models Run</span>
              <span className="text-xl font-bold text-emerald-400 block">
                {detailedUsage.forecasts_total_count.toLocaleString()}
              </span>
              <span className="text-[10px] text-slate-500 block">
                Historical model evaluations
              </span>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 space-y-1">
              <span className="text-slate-400 block text-[11px]">Team Seats Allocated</span>
              <span className="text-xl font-bold text-purple-400 block">
                {detailedUsage.total_seats_used} / {detailedUsage.seats_limit}
              </span>
              <span className="text-[10px] text-slate-500 block">
                {detailedUsage.active_members_count} active accounts
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Plan Comparison Grid */}
      {subDetails && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <h3 className="text-lg font-bold text-white">Available Subscription Tiers</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {subDetails.available_plans.filter(p => p.tier !== 'ENTERPRISE').map((plan) => {
              const isCurrent = subDetails.tier === plan.tier
              const isUpgradeLoading = upgradingTier === plan.tier

              return (
                <div
                  key={plan.tier}
                  className={`bg-surface p-6 rounded-2xl border flex flex-col justify-between space-y-5 transition ${
                    isCurrent
                      ? 'border-primary ring-1 ring-primary/40 shadow-xl shadow-primary/10'
                      : 'border-slate-700 hover:border-slate-600'
                  }`}
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-base font-bold text-white">{plan.name}</h4>
                      {isCurrent && (
                        <span className="text-[10px] font-mono bg-primary/20 text-primary border border-primary/30 px-2 py-0.5 rounded-full font-bold">
                          CURRENT
                        </span>
                      )}
                    </div>

                    <div className="flex items-baseline gap-1 text-white">
                      <span className="text-3xl font-extrabold">${plan.price_monthly}</span>
                      <span className="text-xs text-slate-400 font-medium">/ month</span>
                    </div>

                    <p className="text-xs text-slate-400">{plan.description}</p>

                    <div className="pt-2 border-t border-slate-800 space-y-2 text-xs">
                      {plan.features.map((feat, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-slate-300">
                          <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                          <span>{feat}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-800">
                    {isCurrent ? (
                      <button
                        disabled
                        className="w-full bg-slate-800 text-slate-400 text-xs font-semibold py-2.5 rounded-xl cursor-default"
                      >
                        Active Plan
                      </button>
                    ) : (
                      <button
                        onClick={() => handleUpgrade(plan.tier)}
                        disabled={!isOwner || isUpgradeLoading}
                        className="w-full bg-primary hover:bg-blue-600 disabled:opacity-50 text-white text-xs font-semibold py-2.5 rounded-xl transition shadow-lg shadow-blue-500/20 inline-flex items-center justify-center gap-1.5"
                        title={!isOwner ? 'Only organization owners can change subscription tiers' : undefined}
                      >
                        {isUpgradeLoading ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <ArrowRight className="w-3.5 h-3.5" />
                        )}
                        Upgrade to {plan.tier}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Billing-Ready Notice */}
      <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-start gap-3">
        <ShieldCheck className="w-4 h-4 text-primary shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="text-slate-300 font-semibold block">Billing-Ready Architecture Notice</span>
          <p>
            SalesMind AI enforces server-side plan quotas in real time. Development mode upgrades immediately adjust quota meters and test limits. To activate live credit card processing, configure your production <code className="text-primary font-mono text-[11px]">STRIPE_API_KEY</code> and webhook endpoints.
          </p>
        </div>
      </div>
    </div>
  )
}

