import { Link } from 'react-router-dom'
import { fmtDate } from '../../lib/format.js'
import { offerState, STATE_STYLE } from '../../lib/offerState.js'

/** Carte d'une formation ou d'une salle (catalogue, mes offres, etc.). */
export default function OfferCard({ item: t, canBook, owner, catalogOwner, onBook, onEdit, onDelete }) {
  const state = offerState(t)
  if (state === 'ended') return null

  const isRoom = t.kind === 'room'
  const stateStyle = state !== 'open' ? STATE_STYLE[state] : null

  let action
  if (catalogOwner) {
    action = (
      <span className="shrink-0 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-600">
        Votre offre
      </span>
    )
  } else if (owner) {
    action = (
      <div className="flex shrink-0 gap-2">
        <button className="btn-ghost" onClick={() => onEdit(t)}>
          Éditer
        </button>
        <button className="btn-ghost text-red-600" onClick={() => onDelete(t)}>
          Supprimer
        </button>
      </div>
    )
  } else if (state === 'open') {
    action =
      canBook && t.available_seats > 0 ? (
        <div className="shrink-0">
          <button className="btn-primary w-full sm:w-auto" onClick={() => onBook(t)}>
            Réserver
          </button>
        </div>
      ) : (
        <span className="shrink-0 rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600">{t.status}</span>
      )
  } else {
    const label = state === 'full' && isRoom ? 'Occupée' : stateStyle.label
    action = (
      <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${stateStyle.badge}`}>{label}</span>
    )
  }

  const fillPct = t.shared_seats > 0 ? Math.round((t.booked_seats / t.shared_seats) * 100) : 0
  const fillColor = fillPct >= 90 ? '#ef4444' : fillPct >= 60 ? '#f59e0b' : '#22c55e'

  return (
    <div className={`card flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between ${stateStyle ? stateStyle.card : ''}`}>
      <div className="min-w-0 flex-1">
        <div className="flex min-w-0 items-center gap-2">
          <h3 className="min-w-0 flex-1 truncate font-semibold">{t.title}</h3>
          {t.is_remote ? (
            <span className="dist-badge">À distance</span>
          ) : (
            t.distance_km != null && <span className="dist-badge">📍 {t.distance_km} km</span>
          )}
        </div>
        {!isRoom && (t.tags || []).length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {t.tags.map((tag) => (
              <span key={tag} className="tag-badge">
                {tag}
              </span>
            ))}
          </div>
        )}
        <p className="mt-0.5 truncate text-sm text-gray-500">
          <Link to={`/company?id=${t.provider_id}`} className="text-inherit underline decoration-dotted">
            {t.provider_name}
          </Link>
        </p>
        <p className="mt-2 line-clamp-2 text-sm text-gray-600">{t.description || ''}</p>
        <dl className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-700">
          <div>
            <span className="font-medium text-gray-400">Date</span> · {fmtDate(t.starts_at)}
          </div>
          <div>
            <span className="font-medium text-gray-400">Lieu</span> · {t.location || '—'}
          </div>
          {isRoom ? (
            <div>
              <span className="font-medium text-gray-400">Capacité</span> · <b>{t.shared_seats}</b>{' '}
              personne(s) · {t.price_per_seat} €/résa
            </div>
          ) : (
            <div>
              <span className="font-medium text-gray-400">Places</span> · <b>{t.available_seats}</b>/
              {t.shared_seats} · {t.price_per_seat} €/place
            </div>
          )}
          <div>
            <span className="font-medium text-gray-400">Contact</span> · {t.contact_phone}
          </div>
        </dl>
        {!isRoom && (
          <div className="mt-2 flex items-center gap-2">
            <div className="fill-bar-track">
              <div className="fill-bar-fill" style={{ width: `${fillPct}%`, background: fillColor }} />
            </div>
            <span className="shrink-0 text-[0.65rem] text-gray-500">{fillPct}% occupé</span>
          </div>
        )}
      </div>
      {action}
    </div>
  )
}
