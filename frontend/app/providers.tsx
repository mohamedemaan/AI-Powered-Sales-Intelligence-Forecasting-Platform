'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import api from '../lib/api'

export interface UserProfile {
  id: string
  email: string
  role: string
  is_active: boolean
  tenant_id?: string | null
}

interface AuthContextType {
  user: UserProfile | null
  loading: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
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
      router.push('/')
      return { success: true }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid email or password.'
      return { success: false, error: msg }
    }
  }

  const register = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await api.post('/api/v1/auth/register', {
        email,
        password,
        role: 'ANALYST',
        is_active: true
      })
      return await login(email, password)
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed.'
      return { success: false, error: msg }
    }
  }

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
    }
    setUser(null)
    setLoading(false)
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
