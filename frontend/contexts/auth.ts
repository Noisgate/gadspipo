import { create } from 'zustand'
import Cookies from 'js-cookie'
import { User } from '@/types'
import { apiClient } from '@/lib/api-client'

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  isInitialized: boolean
  
  // Actions
  initAuth: () => Promise<void>
  setToken: (token: string) => void
  setUser: (user: User | null) => void
  logout: () => void
}

export const useAuth = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isLoading: false,
  isInitialized: false,

  initAuth: async () => {
    set({ isLoading: true })
    try {
      // Check if token exists in cookies
      const initialToken = Cookies.get('auth_token')
      
      if (initialToken) {
        set({ token: initialToken })
        // Fetch current user
        try {
          const user = await apiClient.getCurrentUser()
          if (get().token === initialToken) {
            set({ user, isInitialized: true })
          } else {
            set({ isInitialized: true })
          }
        } catch (error) {
          const statusCode =
            typeof error === 'object' &&
            error !== null &&
            'response' in error &&
            typeof error.response === 'object' &&
            error.response !== null &&
            'status' in error.response &&
            typeof error.response.status === 'number'
              ? error.response.status
              : null

          // Only clear the session if the token that failed is still the
          // current one. This avoids wiping a freshly issued OAuth token.
          if (get().token === initialToken && statusCode === 401) {
            Cookies.remove('auth_token')
            set({ user: null, token: null, isInitialized: true })
          } else {
            set({ isInitialized: true })
          }
        }
      } else {
        set({ isInitialized: true })
      }
    } finally {
      set({ isLoading: false })
    }
  },

  setToken: (token: string) => {
    Cookies.set('auth_token', token, {
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      expires: 1, // 1 day
    })
    set({ token, isInitialized: true })
  },

  setUser: (user: User | null) => {
    set({ user })
  },

  logout: () => {
    Cookies.remove('auth_token')
    set({ user: null, token: null })
  },
}))
