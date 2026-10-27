/**
 * Client HTTP Avyro — fetch authentifié vers l'API REST Flask.
 *
 * Tous les tokens sont stockés dans localStorage (avyro_token, avyro_refresh,
 * avyro_user). Sur une réponse 401 (hors mode invité), une seule tentative de
 * refresh (POST /auth/refresh) est faite ; les requêtes concurrentes attendent
 * ce refresh. En cas d'échec, la session est effacée et /login est affiché.
 */
const API_BASE = '/api'

let guestMode = false

export function getToken() {
  return localStorage.getItem('avyro_token')
}

export function setSession(data) {
  if (data.access_token) localStorage.setItem('avyro_token', data.access_token)
  if (data.refresh_token) localStorage.setItem('avyro_refresh', data.refresh_token)
  if (data.user) localStorage.setItem('avyro_user', JSON.stringify(data.user))
}

export function clearSession() {
  localStorage.removeItem('avyro_token')
  localStorage.removeItem('avyro_refresh')
  localStorage.removeItem('avyro_user')
}

/**
 * Révoque côté serveur la session (POST /auth/logout, access en Authorization,
 * refresh dans le corps JSON). Un seul appel, échec silencieux ; à appeler avant clearSession().
 */
export function revokeSession() {
  const access = getToken()
  if (!access) return
  const refresh = localStorage.getItem('avyro_refresh')
  const send = (token) => {
    const headers = { Authorization: `Bearer ${token}` }
    const init = { method: 'POST', headers }
    if (refresh) {
      headers['Content-Type'] = 'application/json'
      init.body = JSON.stringify({ refresh_token: refresh })
    }
    return fetch(`${API_BASE}/auth/logout`, init)
  }
  // Refresh/retry indépendants du localStorage (vidé juste après par clearSession)
  const retry = async () => {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${refresh}` },
    })
    if (!res.ok) return
    const data = await res.json().catch(() => null)
    if (data?.access_token) await send(data.access_token)
  }
  try {
    send(access)
      .then((res) => (res.status === 401 && refresh ? retry() : undefined))
      .catch(() => {})
  } catch {
    /* ignoré */
  }
}

export function currentUser() {
  try {
    const raw = localStorage.getItem('avyro_user')
    return raw ? JSON.parse(raw) : null
  } catch (ex) {
    console.warn('Session locale corrompue', ex)
    clearSession()
    return null
  }
}

export function enableGuestMode() {
  guestMode = true
}

// Routes où un 401 signifie « identifiants invalides », pas « session expirée »
const PUBLIC_AUTH = ['/auth/login', '/auth/register', '/auth/accept-invite', '/auth/refresh']

let refreshPromise = null

/** Renouvelle l'access token (une seule requête partagée). Retourne true si OK. */
function refreshSession() {
  if (refreshPromise) return refreshPromise
  const refresh = localStorage.getItem('avyro_refresh')
  if (!refresh) return Promise.resolve(false)
  refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${refresh}` },
  })
    .then(async (res) => {
      if (!res.ok) return false
      const data = await res.json().catch(() => null)
      if (!data?.access_token) return false
      setSession(data)
      return true
    })
    .catch(() => false)
    .finally(() => {
      refreshPromise = null
    })
  return refreshPromise
}

function rawFetch(path, method, body) {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token && !guestMode) headers.Authorization = `Bearer ${token}`
  return fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * Effectue une requête HTTP vers l'API.
 *
 * @param {string} path    - Chemin relatif à /api, ex. "/auth/login"
 * @param {object} options - { method, body } (body sérialisé en JSON auto)
 * @returns {Promise<any>} - Données JSON de la réponse (null si 204)
 * @throws {Error}         - Enrichi avec .data (corps JSON) et .status (HTTP)
 */
export async function api(path, { method = 'GET', body } = {}) {
  let res = await rawFetch(path, method, body)

  if (res.status === 401 && !guestMode && !PUBLIC_AUTH.some((p) => path.startsWith(p))) {
    if (await refreshSession()) {
      res = await rawFetch(path, method, body)
    }
    if (res.status === 401) {
      clearSession()
      if (location.pathname !== '/login') location.href = '/login'
    }
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) throw Object.assign(new Error('API error'), { data, status: res.status })
  return data
}

/** Extrait un message d'erreur lisible depuis une erreur levée par api(). */
export function errText(ex) {
  return ex.data?.message || (ex.data?.messages && JSON.stringify(ex.data.messages)) || 'Erreur'
}
