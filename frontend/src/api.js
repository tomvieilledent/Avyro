// Client API minimal pour Avyro.
const API_BASE = window.AVYRO_API_BASE || "/api";

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

async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    clearSession();
    if (!location.pathname.endsWith("login.html")) location.href = "login.html";
  }

  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw Object.assign(new Error("API error"), { data, status: res.status });
  return data;
}

function requireAuth() {
  if (!getToken()) location.href = "login.html";
}

window.Avyro = { api, setSession, clearSession, currentUser, requireAuth, getToken };
