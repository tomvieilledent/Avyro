import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, enableGuestMode } from './api.js'
import { MODES } from './modes.js'

const DashboardContext = createContext(null)

export function DashboardProvider({ children }) {
  const [searchParams] = useSearchParams()
  const isGuest = searchParams.get('guest') === '1'
  const modeParam = searchParams.get('mode')

  useEffect(() => {
    if (isGuest) enableGuestMode()
  }, [isGuest])

  useEffect(() => {
    if (modeParam === 'room' || modeParam === 'training') {
      localStorage.setItem('avyro_mode', modeParam)
    }
  }, [modeParam])

  const [mode, setModeState] = useState(() =>
    localStorage.getItem('avyro_mode') === 'room' ? 'room' : 'training',
  )
  const [badgeCount, setBadgeCount] = useState(0)
  const [companyTags, setCompanyTags] = useState([])

  const setMode = useCallback((next) => {
    localStorage.setItem('avyro_mode', next)
    setModeState(next)
  }, [])

  useEffect(() => {
    document.body.classList.toggle('mode-room', mode === 'room')
  }, [mode])

  useEffect(() => {
    if (isGuest) return
    api('/companies/me')
      .then((c) => setCompanyTags(c.tags || []))
      .catch(() => {})
  }, [isGuest])

  const refreshBadges = useCallback(async () => {
    if (isGuest) return
    try {
      const counts = await api('/bookings/counts')
      const key = mode === 'room' ? 'pending_incoming_room' : 'pending_incoming_training'
      setBadgeCount(counts[key] || 0)
    } catch {
      /* silencieux */
    }
  }, [isGuest, mode])

  useEffect(() => {
    refreshBadges()
  }, [refreshBadges])

  const value = useMemo(
    () => ({
      mode,
      setMode,
      MODE: MODES[mode],
      apiBase: mode === 'room' ? '/rooms' : '/trainings',
      kindQS: `kind=${mode}`,
      isGuest,
      badgeCount,
      refreshBadges,
      companyTags,
    }),
    [mode, setMode, isGuest, badgeCount, refreshBadges, companyTags],
  )

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>
}

export function useDashboard() {
  const ctx = useContext(DashboardContext)
  if (!ctx) throw new Error('useDashboard must be used within DashboardProvider')
  return ctx
}
