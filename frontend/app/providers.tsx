'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
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

export interface RegisterData {
  name?: string
  username?: string
  email: string
  password: string
}

interface AuthContextType {
  user: UserProfile | null
  loading: boolean
  login: (usernameOrEmail: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (
    dataOrEmail: RegisterData | string,
    passwordArg?: string
  ) => Promise<{ success: boolean; error?: string }>
  logout: () => void
  fetchUser: () => Promise<void>
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
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  const fetchUser = async () => {
    try {
      const res = await api.get('/api/v1/users/me')
      setUser(res.data)
    } catch (err) {
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
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
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
        is_active: true
      })
      return await login(email, password)
    } catch (err: any) {
      const msg = formatErrorMessage(err, 'Registration failed. Please verify credentials.')
      return { success: false, error: msg }
    }
  }

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
    }
    setUser(null)
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
    <AuthContext.Provider value={{ user, loading, login, register, logout, fetchUser }}>
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
      <AuthProvider>
        {children}
      </AuthProvider>
    </QueryClientProvider>
  )
}
