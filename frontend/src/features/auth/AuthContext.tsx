import { createContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import * as authApi from '../../api/auth'
import { setUnauthorizedHandler } from '../../api/client'
import type { LoginRequest, RegisterRequest, User } from '../../types/user'
import { clearToken, getToken, setToken } from '../../utils/tokenStorage'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (data: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(() => Boolean(getToken()))

  const refreshUser = async () => {
    const currentUser = await authApi.getCurrentUser()
    setUser(currentUser)
  }

  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearToken()
      setUser(null)
    })

    if (getToken()) {
      // Fetch-on-mount to validate the stored token; setState happens in the
      // promise resolution, not synchronously in the effect body.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      refreshUser()
        .catch(() => {
          clearToken()
          setUser(null)
        })
        .finally(() => setIsLoading(false))
    }

    return () => setUnauthorizedHandler(null)
  }, [])

  const login = async (data: LoginRequest) => {
    const token = await authApi.login(data)
    setToken(token.access_token)
    await refreshUser()
  }

  const register = async (data: RegisterRequest) => {
    await authApi.register(data)
    await login({ email: data.email, password: data.password })
  }

  const logout = () => {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
