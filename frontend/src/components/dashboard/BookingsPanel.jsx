import { useCallback, useEffect, useState } from 'react'
import { api, errText } from '../../lib/api.js'
import { useDashboard } from '../../lib/DashboardContext.jsx'
import { useToast } from '../../lib/ToastContext.jsx'

export default function BookingsPanel() {
  const { kindQS } = useDashboard()
  const showToast = useToast()
  const [items, setItems] = useState([])

  const load = useCallback(async () => {
    const list = await api(`/bookings?${kindQS}`)
    setItems(list)
  }, [kindQS])

  useEffect(() => {
    load()
  }, [load])

  async function unsubscribe(b) {
    if (!confirm('Se désinscrire de cette formation ?')) return
    try {
      await api(`/bookings/${b.id}`, { method: 'DELETE' })
      load()
    } catch (ex) {
      showToast(errText(ex), 'error')
    }
  }

  return (
    <section className="pt-7">
      <div className="panel-hd mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2>Mes réservations</h2>
          <p>Demandes de réservation effectuées par votre structure.</p>
        </div>
      </div>
      <div className="content-list">
        {items.map((b) => (
          <div key={b.id} className="card flex items-center justify-between gap-3">
            <div className="min-w-0">
              <b>{b.training_title}</b> — {b.seats} place(s)
              <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">{b.status}</span>
            </div>
            {b.status === 'pending' && (
              <button className="btn-ghost shrink-0 text-red-600" onClick={() => unsubscribe(b)}>
                Se désinscrire
              </button>
            )}
          </div>
        ))}
        {!items.length && <p className="text-sm text-gray-500">Aucune réservation.</p>}
      </div>
    </section>
  )
}
