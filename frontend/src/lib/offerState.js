/**
 * Détermine l'état visuel d'une formation/salle à partir de ses données.
 *   "ended"   — date de fin dépassée (ne doit plus être affiché)
 *   "running" — en cours (date de début dépassée mais pas la fin)
 *   "full"    — complet (0 place disponible)
 *   "open"    — normal, places disponibles
 */
export function offerState(item) {
  const now = new Date()
  if (now >= new Date(item.ends_at)) return 'ended'
  if (now >= new Date(item.starts_at)) return 'running'
  if (item.available_seats <= 0) return 'full'
  return 'open'
}

export const STATE_STYLE = {
  full: {
    card: 'border-yellow-300 bg-yellow-50 opacity-90',
    badge: 'bg-yellow-100 text-yellow-800',
    label: 'Complète',
  },
  running: {
    card: 'border-blue-200 bg-blue-50 opacity-90',
    badge: 'bg-blue-100 text-blue-800',
    label: 'En cours',
  },
}
