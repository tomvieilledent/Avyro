import { useCallback, useEffect, useState } from 'react'
import { api, errText } from '../../lib/api.js'
import { useDashboard } from '../../lib/DashboardContext.jsx'
import { useToast } from '../../lib/ToastContext.jsx'

export default function IncomingPanel() {
  const { kindQS, refreshBadges } = useDashboard()
  const showToast = useToast()
  const [items, setItems] = useState([])

  const load = useCallback(async () => {
    const list = await api(`/bookings/incoming?${kindQS}`)
    setItems(list)
  }, [kindQS])

  useEffect(() => {
    load()
  }, [load])

  async function setStatus(booking, status) {
    try {
      await api(`/bookings/${booking.id}`, { method: 'PATCH', body: { status } })
      load()
      refreshBadges()
    } catch (ex) {
      showToast(errText(ex), 'error')
    }
  }

  return (
    <section className="pt-7">
      <div className="panel-hd mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2>Demandes reçues</h2>
          <p>Réservations à confirmer ou refuser sur vos offres.</p>
        </div>
      </div>
      <div className="content-list">
        {items.map((b) => (
          <div key={b.id} className="card flex items-center justify-between gap-3">
            <div>
              <b>{b.company_name}</b> · {b.training_title} — {b.seats} place(s)
              {b.note && (
                <>
                  <br />
                  <span className="text-xs text-gray-400 italic">"{b.note}"</span>
                </>
              )}
            </div>
            {b.status === 'pending' ? (
              <div className="flex shrink-0 gap-2">
                <button className="btn-primary" onClick={() => setStatus(b, 'confirmed')}>
                  Confirmer
                </button>
                <button className="btn-ghost" onClick={() => setStatus(b, 'cancelled')}>
                  Refuser
                </button>
              </div>
            ) : (
              <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs">{b.status}</span>
            )}
          </div>
        ))}
        {!items.length && <p className="text-sm text-gray-500">Aucune demande.</p>}
      </div>
    </section>
  )
}
