import { useCallback, useEffect, useState } from 'react'
import { api, errText } from '../../lib/api.js'
import { useDashboard } from '../../lib/DashboardContext.jsx'
import { useToast } from '../../lib/ToastContext.jsx'
import OfferCard from './OfferCard.jsx'
import OfferFormModal from './OfferFormModal.jsx'

export default function MinePanel() {
  const { MODE, apiBase } = useDashboard()
  const showToast = useToast()
  const [items, setItems] = useState([])
  const [formTarget, setFormTarget] = useState(undefined) // undefined = closed, null = create, object = edit

  const load = useCallback(async () => {
    const list = await api(`${apiBase}?mine=true`)
    setItems(list)
  }, [apiBase])

  useEffect(() => {
    load()
  }, [load])

  async function handleDelete(item) {
    if (!confirm(MODE.deleteConfirm(item))) return
    try {
      await api(`${apiBase}/${item.id}`, { method: 'DELETE' })
      load()
    } catch (ex) {
      showToast(errText(ex), 'error')
    }
  }

  function handleSaved() {
    setFormTarget(undefined)
    load()
  }

  return (
    <section className="pt-7">
      <div className="panel-hd mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2>Mes offres publiées</h2>
          <p>Formations et salles que vous proposez à la mutualisation.</p>
        </div>
        <button className="btn-primary shrink-0" onClick={() => setFormTarget(null)}>
          {MODE.newBtn}
        </button>
      </div>
      <div className="content-grid">
        {items.map((t) => (
          <OfferCard key={t.id} item={t} owner onEdit={setFormTarget} onDelete={handleDelete} />
        ))}
        {!items.length && <p className="text-sm text-gray-500">{MODE.mineEmpty}</p>}
      </div>

      {formTarget !== undefined && (
        <OfferFormModal editing={formTarget} onClose={() => setFormTarget(undefined)} onSaved={handleSaved} />
      )}
    </section>
  )
}
