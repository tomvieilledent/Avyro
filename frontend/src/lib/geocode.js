import { api } from './api.js'

/** Recherche d'adresse via le backend (proxy de géocodage). Retourne [{label, lat, lng, line1, postal_code, city}]. */
export async function searchAddress(query) {
  const data = await api(`/geocode?q=${encodeURIComponent(query)}`)
  return Array.isArray(data) ? data : []
}
