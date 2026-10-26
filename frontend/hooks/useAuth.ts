'use client'

import { useAuthContext, UserProfile, RegisterData } from '../app/providers'

export type { UserProfile, RegisterData }
export const useAuth = useAuthContext
export default useAuth
