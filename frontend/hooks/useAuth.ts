'use client'

import { useAuthContext, UserProfile, RegisterData, Organization } from '../app/providers'

export type { UserProfile, RegisterData, Organization }
export const useAuth = useAuthContext
export default useAuth
