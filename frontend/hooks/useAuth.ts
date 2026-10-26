'use client'

import { useAuthContext, UserProfile } from '../app/providers'

export type { UserProfile }
export const useAuth = useAuthContext
export default useAuth
