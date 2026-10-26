'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { QueryClient, QueryClientProvider, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import api from '../lib/api'

export interface UserProfile {
  id: string
  email: string
  username?: string | null
  full_name?: string | null
  role: string
  is_active: boolean
  tenant_id?: string | null
}

export interface Organization {
  id: string
  name: string
  slug?: string | null
  owner_id?: string | null
  subscription_tier: string
  subscription_status: string
  role: string
  is_active: boolean
  members_count: number
  created_at: string
}

export interface RegisterData {
  name?: string
  username?: string
  email: string
  password: string
}

interface AuthContextType {
  user: UserProfile | null
  loading: boolean
  organizations: Organization[]
  activeOrg: Organization | null
  login: (usernameOrEmail: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (
    dataOrEmail: RegisterData | string,
    passwordArg?: string
  ) => Promise<{ success: boolean; error?: string }>
  logout: () => void
  fetchUser: () => Promise<void>
  refreshOrganizations: () => Promise<void>
  switchOrganization: (orgId: string) => Promise<{ success: boolean; error?: string }>
  createOrganization: (name: string, slug?: string) => Promise<{ success: boolean; error?: string; organization?: Organization }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuthContext = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  return context
}

function formatErrorMessage(err: any, fallback: string): string {
  const detail = err.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item: any) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && item.msg) {
          return String(item.msg).replace(/^Value error,\s*/i, '')
        }
        return JSON.stringify(item)
      })
      .filter(Boolean)
      .join('. ')
  }
  if (detail && typeof detail === 'object') {
    if (detail.msg) {
      return String(detail.msg).replace(/^Value error,\s*/i, '')
    }
    return JSON.stringify(detail)
  }
  if (err.response?.data?.message) {
    return String(err.response.data.message)
  }
  if (err.message && typeof err.message === 'string') {
    return err.message
  }
  return fallback
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [activeOrg, setActiveOrg] = useState<Organization | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const queryClient = useQueryClient()

  const refreshOrganizations = async () => {
    try {
      const res = await api.get('/api/v1/organizations')
      const orgs: Organization[] = res.data || []
      setOrganizations(orgs)
      const active = orgs.find((o) => o.is_active) || orgs[0] || null
      setActiveOrg(active)
      if (active && typeof window !== 'undefined') {
        localStorage.setItem('active_organization_id', active.id)
      }
    } catch {
      // Organization fetch gracefully ignores unauthenticated state
    }
  }

  const fetchUser = async () => {
    try {
      const res = await api.get('/api/v1/users/me')
      setUser(res.data)
      await refreshOrganizations()
    } catch {
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const res = await api.post('/api/v1/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })

      if (typeof window !== 'undefined') {
        localStorage.setItem('token', res.data.access_token)
      }

      await fetchUser()
      router.push('/dashboard')
      return { success: true }
    } catch (err: any) {
      const msg = formatErrorMessage(err, 'Invalid email or password.')
      return { success: false, error: msg }
    }
  }

  const register = async (
    dataOrEmail: RegisterData | string,
    passwordArg?: string
  ): Promise<{ success: boolean; error?: string }> => {
    try {
      const email = typeof dataOrEmail === 'string' ? dataOrEmail : dataOrEmail.email
      const password = typeof dataOrEmail === 'string' ? (passwordArg || '') : dataOrEmail.password
      const name = typeof dataOrEmail === 'object' ? dataOrEmail.name : undefined
      const username = typeof dataOrEmail === 'object' ? dataOrEmail.username : undefined

      await api.post('/api/v1/auth/register', {
        email,
        password,
        username: username || email.split('@')[0],
        full_name: name || undefined,
        role: 'ANALYST',
        is_active: true,
      })
      return await login(email, password)
    } catch (err: any) {
      const msg = formatErrorMessage(err, 'Registration failed. Please verify credentials.')
      return { success: false, error: msg }
    }
  }

  const switchOrganization = async (orgId: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await api.post('/api/v1/organizations/switch', { organization_id: orgId })
      if (typeof window !== 'undefined') {
        localStorage.setItem('active_organization_id', orgId)
      }
      await fetchUser()
      await refreshOrganizations()
      // Invalidate all cached dashboard/sales data queries so components reload cleanly
      queryClient.invalidateQueries()
      return { success: true }
    } catch (err: any) {
      const msg = formatErrorMessage(err, 'Failed to switch workspace context.')
      return { success: false, error: msg }
    }
  }

  const createOrganization = async (
    name: string,
    slug?: string
  ): Promise<{ success: boolean; error?: string; organization?: Organization }> => {
    try {
      const res = await api.post('/api/v1/organizations', {
        name,
        slug: slug?.trim() || undefined,
      })
      const newOrg: Organization = res.data
      if (typeof window !== 'undefined') {
        localStorage.setItem('active_organization_id', newOrg.id)
      }
      await fetchUser()
      await refreshOrganizations()
      queryClient.invalidateQueries()
      return { success: true, organization: newOrg }
    } catch (err: any) {
      const msg = formatErrorMessage(err, 'Failed to create workspace.')
      return { success: false, error: msg }
    }
  }

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
      localStorage.removeItem('active_organization_id')
    }
    setUser(null)
    setOrganizations([])
    setActiveOrg(null)
    setLoading(false)
    router.push('/')
  }

  useEffect(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('token')) {
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        organizations,
        activeOrg,
        login,
        register,
        logout,
        fetchUser,
        refreshOrganizations,
        switchOrganization,
        createOrganization,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export default function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}
