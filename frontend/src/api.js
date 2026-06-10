/**
 * api.js — Client HTTP Avyro
 *
 * Expose l'objet global `window.Avyro` avec :
 *   - api(path, options)    : fetch authentifié vers l'API REST
 *   - setSession(data)      : persiste access_token, refresh_token et user
 *   - clearSession()        : efface la session (logout)
 *   - currentUser()         : retourne l'objet user depuis localStorage
 *   - requireAuth()         : redirige vers login.html si aucun token présent
 *   - getToken()            : retourne l'access token brut
 *
 * Tous les tokens sont stockés dans localStorage (clés : avyro_token,
 * avyro_refresh, avyro_user). Sur une réponse 401, la session est effacée
 * et l'utilisateur est renvoyé vers login.html automatiquement.
 */
const API_BASE = window.AVYRO_API_BASE || "/api";
let _guestMode = false;

function getToken() {
  return localStorage.getItem("avyro_token");
}

function setSession(data) {
  if (data.access_token) localStorage.setItem("avyro_token", data.access_token);
  if (data.refresh_token)
    localStorage.setItem("avyro_refresh", data.refresh_token);
  if (data.user) localStorage.setItem("avyro_user", JSON.stringify(data.user));
}

function clearSession() {
  localStorage.removeItem("avyro_token");
  localStorage.removeItem("avyro_refresh");
  localStorage.removeItem("avyro_user");
}

function currentUser() {
  const raw = localStorage.getItem("avyro_user");
  return raw ? JSON.parse(raw) : null;
}

/**
 * Effectue une requête HTTP vers l'API.
 *
 * @param {string} path    - Chemin relatif à API_BASE, ex. "/auth/login"
 * @param {object} options - { method, body } (body sérialisé en JSON auto)
 * @returns {Promise<any>} - Données JSON de la réponse (null si 204)
 * @throws {Error}         - Enrichi avec .data (corps JSON) et .status (HTTP)
 */
async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token && !_guestMode) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // 401 → session expirée ou invalide : déconnexion et redirection
  if (res.status === 401 && !_guestMode) {
    clearSession();
    if (!location.pathname.endsWith("login.html")) location.href = "login.html";
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw Object.assign(new Error("API error"), { data, status: res.status });
  return data;
}

/** Redirige vers login.html si aucun access token n'est stocké. */
function requireAuth() {
  if (!getToken()) location.href = "login.html";
}

function enableGuestMode() { _guestMode = true; }

window.Avyro = { api, setSession, clearSession, currentUser, requireAuth, getToken, enableGuestMode };
