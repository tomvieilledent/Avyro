import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from './api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => api.currentUser())

  const login = useCallback((data) => {
    api.setSession(data)
    setUser(data.user)
  }, [])

  const logout = useCallback(() => {
    api.clearSession()
    setUser(null)
  }, [])

  const refreshUser = useCallback((data) => {
    localStorage.setItem('avyro_user', JSON.stringify(data))
    setUser(data)
  }, [])

  const value = useMemo(
    () => ({ user, isAuthenticated: !!user, login, logout, refreshUser }),
    [user, login, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

/** Redirige vers /login si aucun utilisateur n'est authentifié (mode invité excepté). */
export function useRequireAuth({ guest = false } = {}) {
  const { user } = useAuth()
  const navigate = useNavigate()
  useEffect(() => {
    if (!guest && !user && !api.getToken()) {
      navigate('/login', { replace: true })
    }
  }, [guest, user, navigate])
}
