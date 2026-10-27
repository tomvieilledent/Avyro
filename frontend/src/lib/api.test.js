import { vi } from 'vitest'
import { api, setSession, getToken, revokeSession } from './api.js'

const json = (status, body) => new Response(JSON.stringify(body), { status })

beforeEach(() => {
  localStorage.clear()
  setSession({ access_token: 'old', refresh_token: 'ref' })
  vi.stubGlobal('fetch', vi.fn())
})
afterEach(() => vi.unstubAllGlobals())

describe('api()', () => {
  it('envoie le bearer et renvoie le JSON', async () => {
    fetch.mockResolvedValueOnce(json(200, { ok: 1 }))
    expect(await api('/x')).toEqual({ ok: 1 })
    expect(fetch.mock.calls[0][0]).toBe('/api/x')
    expect(fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer old')
  })

  it('refresh transparent sur 401 puis rejoue la requête', async () => {
    fetch.mockImplementation(async (url, opts) => {
      if (url === '/api/auth/refresh') return json(200, { access_token: 'new' })
      return opts.headers.Authorization === 'Bearer new' ? json(200, { ok: true }) : json(401, {})
    })
    expect(await api('/data')).toEqual({ ok: true })
    expect(getToken()).toBe('new')
    expect(fetch.mock.calls.filter(([u]) => u === '/api/auth/refresh')[0][1].headers.Authorization).toBe(
      'Bearer ref',
    )
  })

  it('met en file les 401 concurrents : un seul refresh', async () => {
    fetch.mockImplementation(async (url, opts) => {
      if (url === '/api/auth/refresh') {
        await new Promise((r) => setTimeout(r, 10))
        return json(200, { access_token: 'new' })
      }
      return opts.headers.Authorization === 'Bearer new' ? json(200, { u: url }) : json(401, {})
    })
    const res = await Promise.all([api('/a'), api('/b'), api('/c')])
    expect(res.map((r) => r.u)).toEqual(['/api/a', '/api/b', '/api/c'])
    expect(fetch.mock.calls.filter(([u]) => u === '/api/auth/refresh')).toHaveLength(1)
  })

  it('échec du refresh : session effacée et erreur 401', async () => {
    vi.stubGlobal('location', { pathname: '/login', href: '' })
    fetch.mockImplementation(async () => json(401, { message: 'no' }))
    await expect(api('/data')).rejects.toMatchObject({ status: 401 })
    expect(getToken()).toBeNull()
  })

  it('pas de refresh sur les routes publiques', async () => {
    fetch.mockResolvedValueOnce(json(401, { message: 'bad' }))
    await expect(api('/auth/login', { method: 'POST', body: {} })).rejects.toMatchObject({ status: 401 })
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})

describe('revokeSession()', () => {
  it('fait un seul appel /auth/logout (access en bearer, refresh en corps), sans lever en cas d’échec', () => {
    fetch.mockRejectedValue(new Error('net'))
    expect(() => revokeSession()).not.toThrow()
    expect(fetch).toHaveBeenCalledTimes(1)
    const [url, opts] = fetch.mock.calls[0]
    expect(url).toBe('/api/auth/logout')
    expect(opts.headers.Authorization).toBe('Bearer old')
    expect(JSON.parse(opts.body)).toEqual({ refresh_token: 'ref' })
  })

  it('401 sur logout : refresh puis un seul retry avec le nouvel access', async () => {
    fetch.mockImplementation(async (url, opts) => {
      if (url === '/api/auth/refresh') return json(200, { access_token: 'new' })
      return opts.headers.Authorization === 'Bearer new' ? json(200, {}) : json(401, {})
    })
    revokeSession()
    await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(3))
    expect(fetch.mock.calls[1][0]).toBe('/api/auth/refresh')
    expect(fetch.mock.calls[2][0]).toBe('/api/auth/logout')
    expect(fetch.mock.calls[2][1].headers.Authorization).toBe('Bearer new')
  })

  it('401 sur logout puis refresh en échec : silencieux', async () => {
    fetch.mockImplementation(async () => json(401, {}))
    revokeSession()
    await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
  })
})
