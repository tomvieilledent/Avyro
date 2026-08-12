/**
 * Client HTTP Avyro — fetch authentifié vers l'API REST Flask.
 *
 * Tous les tokens sont stockés dans localStorage (avyro_token, avyro_refresh,
 * avyro_user). Sur une réponse 401 (hors mode invité), la session est effacée
 * et l'utilisateur est renvoyé vers /login.
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

export function currentUser() {
  const raw = localStorage.getItem('avyro_user')
  return raw ? JSON.parse(raw) : null
}

export function enableGuestMode() {
  guestMode = true
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
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token && !guestMode) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401 && !guestMode) {
    clearSession()
    if (location.pathname !== '/login') location.href = '/login'
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) throw Object.assign(new Error('API error'), { data, status: res.status })
  return data
}

/** Extrait un message d'erreur lisible depuis une erreur levée par api(). */
export function errText(ex) {
  return ex.data?.message || (ex.data?.messages && JSON.stringify(ex.data.messages)) || 'Erreur'
}
