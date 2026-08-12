/** Formate une date ISO en format français (ex. "1 sept. 2026 à 09:00"). */
export function fmtDate(s) {
  return new Date(s).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })
}
