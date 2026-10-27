import { vi } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext.jsx'

const wrapper = ({ children }) => (
  <MemoryRouter>
    <AuthProvider>{children}</AuthProvider>
  </MemoryRouter>
)
const session = { access_token: 'a', refresh_token: 'r', user: { id: 1, name: 'Zoé' } }

beforeEach(() => vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(new Response('{}')))))
afterEach(() => vi.unstubAllGlobals())

describe('AuthContext', () => {
  it('login stocke la session et expose l’utilisateur', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.isAuthenticated).toBe(false)
    act(() => result.current.login(session))
    expect(result.current.user).toEqual(session.user)
    expect(localStorage.getItem('avyro_token')).toBe('a')
  })

  it('restaure l’utilisateur depuis localStorage', () => {
    localStorage.setItem('avyro_user', JSON.stringify(session.user))
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.isAuthenticated).toBe(true)
  })

  it('logout appelle /auth/logout et nettoie localement', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    act(() => result.current.login(session))
    act(() => result.current.logout())
    expect(fetch.mock.calls.map(([u]) => u)).toEqual(['/api/auth/logout'])
    expect(result.current.user).toBeNull()
    expect(localStorage.getItem('avyro_token')).toBeNull()
    expect(localStorage.getItem('avyro_refresh')).toBeNull()
  })

  it('logout nettoie même si le réseau échoue', () => {
    fetch.mockRejectedValue(new Error('net'))
    const { result } = renderHook(() => useAuth(), { wrapper })
    act(() => result.current.login(session))
    act(() => result.current.logout())
    expect(result.current.user).toBeNull()
    expect(localStorage.getItem('avyro_user')).toBeNull()
  })

  it('refreshUser remplace les tokens sans les garder dans l’utilisateur', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    act(() => result.current.login(session))
    act(() =>
      result.current.refreshUser({ id: 1, name: 'Zoé', access_token: 'a2', refresh_token: 'r2' }),
    )
    expect(result.current.user).toEqual({ id: 1, name: 'Zoé' })
    expect(JSON.parse(localStorage.getItem('avyro_user'))).toEqual({ id: 1, name: 'Zoé' })
    expect(localStorage.getItem('avyro_token')).toBe('a2')
    expect(localStorage.getItem('avyro_refresh')).toBe('r2')
  })
})
