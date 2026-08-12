import { useEffect, useRef, useState } from 'react'
import { api, errText } from '../../lib/api.js'
import { searchAddress } from '../../lib/nominatim.js'
import { useDashboard } from '../../lib/DashboardContext.jsx'
import { useToast } from '../../lib/ToastContext.jsx'

const EMPTY_FORM = {
  title: '',
  tags: '',
  description: '',
  contact_phone: '',
  starts_at: '',
  ends_at: '',
  shared_seats: '',
  price_per_seat: '',
  addr_line1: '',
  postal_code: '',
  city: '',
}

/** Parse "line1[ — line2], CP Ville" en { line1, postalCode, city }. */
function parseLocation(loc) {
  const match = loc.match(/,?\s*(\d{4,5})\s+(.+)$/)
  if (!match) return { line1: loc, postalCode: '', city: '' }
  const before = loc.slice(0, loc.length - match[0].length)
  return { line1: before.split(' — ')[0].trim(), postalCode: match[1], city: match[2].trim() }
}

/** Modale de création / édition d'une formation ou d'une salle. */
export default function OfferFormModal({ editing, onClose, onSaved }) {
  const { mode, MODE, apiBase, companyTags } = useDashboard()
  const showToast = useToast()
  const isEdit = !!editing?.id
  const [form, setForm] = useState(EMPTY_FORM)
  const [geo, setGeo] = useState({ lat: null, lng: null })
  const [error, setError] = useState('')
  const [addrQuery, setAddrQuery] = useState('')
  const [addrResults, setAddrResults] = useState([])
  const addrTimer = useRef(null)

  useEffect(() => {
    setError('')
    setAddrQuery('')
    setAddrResults([])
    if (isEdit) {
      const loc = !editing.is_remote && editing.location ? parseLocation(editing.location) : null
      setForm({
        title: editing.title,
        tags: (editing.tags || []).join(', '),
        description: editing.description || '',
        contact_phone: editing.contact_phone || '',
        starts_at: editing.starts_at.slice(0, 16),
        ends_at: editing.ends_at.slice(0, 16),
        shared_seats: editing.shared_seats,
        price_per_seat: editing.price_per_seat,
        addr_line1: loc?.line1 || '',
        postal_code: loc?.postalCode || '',
        city: loc?.city || '',
      })
      setGeo({ lat: editing.latitude || null, lng: editing.longitude || null })
    } else {
      setForm({ ...EMPTY_FORM, tags: companyTags.join(', ') })
      setGeo({ lat: null, lng: null })
    }
  }, [editing, isEdit, companyTags])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function onAddrInput(value) {
    setAddrQuery(value)
    clearTimeout(addrTimer.current)
    if (value.trim().length < 5) {
      setAddrResults([])
      return
    }
    addrTimer.current = setTimeout(async () => {
      try {
        const data = await searchAddress(value.trim())
        setAddrResults(data)
      } catch {
        setAddrResults([])
      }
    }, 400)
  }

  function pickAddress(item) {
    const a = item.address || {}
    const line1 = [a.house_number, a.road].filter(Boolean).join(' ')
    setForm((f) => ({
      ...f,
      addr_line1: line1,
      postal_code: a.postcode || '',
      city: a.city || a.town || a.village || a.municipality || '',
    }))
    setGeo({ lat: parseFloat(item.lat), lng: parseFloat(item.lon) })
    setAddrQuery('')
    setAddrResults([])
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    const line1 = form.addr_line1.trim()
    const cp = form.postal_code.trim()
    const city = form.city.trim()
    const body = {
      title: form.title,
      description: form.description,
      contact_phone: form.contact_phone,
      starts_at: form.starts_at,
      ends_at: form.ends_at,
      shared_seats: parseInt(form.shared_seats, 10),
      price_per_seat: parseFloat(form.price_per_seat || '0'),
      tags: form.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    }
    if (!line1 && !cp) {
      body.is_remote = true
      body.location = 'À distance'
      body.latitude = null
      body.longitude = null
    } else {
      body.is_remote = false
      body.location = [line1, cp && city ? `${cp} ${city}` : cp || city].filter(Boolean).join(', ')
      body.latitude = geo.lat
      body.longitude = geo.lng
    }
    try {
      if (isEdit) {
        await api(`${apiBase}/${editing.id}`, { method: 'PATCH', body })
      } else {
        await api(apiBase, { method: 'POST', body })
      }
      onSaved()
    } catch (ex) {
      setError(errText(ex))
      showToast(errText(ex), 'error')
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/40 p-4 [backdrop-filter:blur(2px)]"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal-inner max-h-[90vh] w-full max-w-[520px] overflow-y-auto rounded-2xl border border-[#e2e8f0] bg-white [box-shadow:0_24px_64px_rgba(15,23,62,0.14),0_4px_16px_rgba(15,23,62,0.06)]">
        <div className="modal-head rounded-t-2xl border-b border-white/15 px-6 py-5 [background:linear-gradient(135deg,#1d4ed8_0%,#3b82f6_100%)]">
          <h2 className="m-0 text-base font-semibold tracking-[-0.01em] text-white">
            {isEdit ? MODE.modalEdit : MODE.modalNew}
          </h2>
        </div>
        <div className="modal-body p-6">
          <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1 text-xs text-gray-500 sm:col-span-2">
              <span>
                Titre <span className="text-red-500">*</span>
              </span>
              <input
                className="input"
                placeholder={MODE.titlePlaceholder}
                required
                value={form.title}
                onChange={(e) => set('title', e.target.value)}
              />
            </label>
            {mode !== 'room' && (
              <input
                className="input sm:col-span-2"
                placeholder="Tags séparés par des virgules (ex: IT, management, sécurité)"
                value={form.tags}
                onChange={(e) => set('tags', e.target.value)}
              />
            )}
            <textarea
              className="input resize-y sm:col-span-2"
              placeholder="Description"
              rows={3}
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
            />
            <div className="relative sm:col-span-2">
              <input
                className="input"
                placeholder="Rechercher une adresse… (laisser vide si à distance)"
                autoComplete="off"
                value={addrQuery}
                onChange={(e) => onAddrInput(e.target.value)}
              />
              {addrResults.length > 0 && (
                <div className="absolute top-[calc(100%+4px)] right-0 left-0 z-[200] max-h-[220px] overflow-y-auto rounded-lg border border-[#e2e8f0] bg-white [box-shadow:0_4px_16px_rgba(0,0,0,0.12)]">
                  {addrResults.map((item, i) => (
                    <div
                      key={i}
                      className="addr-result"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => pickAddress(item)}
                    >
                      {item.display_name}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <input
              className="input cursor-default pointer-events-none bg-[#e2e8f0] text-[#64748b] select-none sm:col-span-2"
              placeholder="Adresse"
              readOnly
              tabIndex={-1}
              value={form.addr_line1}
            />
            <input
              className="input cursor-default pointer-events-none bg-[#e2e8f0] text-[#64748b] select-none"
              placeholder="Code postal"
              maxLength={10}
              readOnly
              tabIndex={-1}
              value={form.postal_code}
            />
            <input
              className="input cursor-default pointer-events-none bg-[#e2e8f0] text-[#64748b] select-none"
              placeholder="Ville"
              readOnly
              tabIndex={-1}
              value={form.city}
            />
            <label className="flex flex-col gap-1 text-xs text-gray-500 sm:col-span-2">
              <span>
                Numéro de contact <span className="text-red-500">*</span>
              </span>
              <input
                className="input"
                type="tel"
                placeholder="Numéro de contact"
                required
                value={form.contact_phone}
                onChange={(e) => set('contact_phone', e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              <span>
                Début <span className="text-red-500">*</span>
              </span>
              <input
                className="input"
                type="datetime-local"
                required
                value={form.starts_at}
                onChange={(e) => set('starts_at', e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              <span>
                Fin <span className="text-red-500">*</span>
              </span>
              <input
                className="input"
                type="datetime-local"
                required
                value={form.ends_at}
                onChange={(e) => set('ends_at', e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              <span>
                {MODE.seatsLabel} <span className="text-red-500">*</span>
              </span>
              <input
                className="input"
                type="number"
                min="1"
                required
                value={form.shared_seats}
                onChange={(e) => set('shared_seats', e.target.value)}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-500">
              Prix / place (€)
              <input
                className="input"
                type="number"
                min="0"
                step="0.01"
                value={form.price_per_seat}
                onChange={(e) => set('price_per_seat', e.target.value)}
              />
            </label>
            {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
            <div className="mt-2 flex justify-end gap-2 sm:col-span-2">
              <button type="button" className="btn-ghost" onClick={onClose}>
                Annuler
              </button>
              <button type="submit" className="btn-primary">
                {isEdit ? 'Enregistrer' : 'Créer'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
