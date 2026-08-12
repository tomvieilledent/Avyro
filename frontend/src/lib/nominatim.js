/** Recherche d'adresse via Nominatim (OpenStreetMap), limitée à la France. */
export async function searchAddress(query) {
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&countrycodes=fr&limit=5`
  const res = await fetch(url, { headers: { 'Accept-Language': 'fr' } })
  return res.json()
}
