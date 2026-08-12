import { useCallback, useEffect, useRef, useState } from 'react'
import { api, errText } from '../../lib/api.js'
import { useAuth } from '../../lib/AuthContext.jsx'
import { useDashboard } from '../../lib/DashboardContext.jsx'
import { useToast } from '../../lib/ToastContext.jsx'
import OfferCard from './OfferCard.jsx'
import BookingModal from './BookingModal.jsx'
import CalendarView from './CalendarView.jsx'

export default function CatalogPanel() {
  const { mode, MODE, apiBase, isGuest, refreshBadges } = useDashboard()
  const { user } = useAuth()
  const showToast = useToast()

  const [items, setItems] = useState([])
  const [tagOptions, setTagOptions] = useState([])
  const [view, setView] = useState('list')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [bookingTarget, setBookingTarget] = useState(null)

  const [search, setSearch] = useState('')
  const [tag, setTag] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [priceMax, setPriceMax] = useState('')
  const [seatsMin, setSeatsMin] = useState('')
  const [remoteOnly, setRemoteOnly] = useState(false)

  const [geoActive, setGeoActive] = useState(false)
  const [geoCoords, setGeoCoords] = useState({ lat: null, lng: null })
  const [geoLoading, setGeoLoading] = useState(false)
  const [radius, setRadius] = useState('25')

  const searchTimer = useRef(null)

  const load = useCallback(async () => {
    const params = new URLSearchParams()
    if (search) params.set('q', search)
    if (tag) params.set('tag', tag)
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    if (priceMax) params.set('price_max', priceMax)
    if (seatsMin) params.set('seats_min', seatsMin)
    if (remoteOnly) params.set('remote_only', 'true')
    if (geoActive && geoCoords.lat != null) {
      params.set('lat', String(geoCoords.lat))
      params.set('lng', String(geoCoords.lng))
      params.set('radius', radius)
    }
    const qs = params.toString()
    const list = await api(`${apiBase}${qs ? '?' + qs : ''}`)
    setItems(list)
    if (!tag) {
      setTagOptions([...new Set(list.flatMap((t) => t.tags || []))].sort())
    }
  }, [apiBase, search, tag, dateFrom, dateTo, priceMax, seatsMin, remoteOnly, geoActive, geoCoords, radius])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(load, 300)
    return () => clearTimeout(searchTimer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search])

  function requestGeo() {
    if (geoActive) {
      setGeoActive(false)
      setGeoCoords({ lat: null, lng: null })
      return
    }
    if (!navigator.geolocation) {
      showToast('Géolocalisation non supportée par ce navigateur.', 'error')
      return
    }
    setGeoLoading(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setGeoActive(true)
        setGeoLoading(false)
      },
      () => {
        setGeoLoading(false)
        showToast('Impossible d’obtenir votre position. Vérifiez les permissions.', 'error')
      },
      { enableHighAccuracy: false, timeout: 8000 },
    )
  }

  function resetAdvanced() {
    setDateFrom('')
    setDateTo('')
    setPriceMax('')
    setSeatsMin('')
    setRemoteOnly(false)
  }

  async function confirmBooking(payload) {
    const target = bookingTarget
    setBookingTarget(null)
    try {
      const body =
        mode === 'room'
          ? { room_id: target.id, seats: target.available_seats, note: payload.note }
          : { training_id: target.id, seats: payload.seats, note: payload.note }
      await api('/bookings', { method: 'POST', body })
      showToast('Demande envoyée avec succès.')
      load()
      refreshBadges()
    } catch (ex) {
      showToast(errText(ex), 'error')
    }
  }

  const visibleCount = items.length

  return (
    <section className="pt-7">
      <div className="filter-bar mb-5 flex flex-wrap items-center gap-[0.625rem]">
        <div className="relative min-w-[180px] flex-1">
          <svg
            className="pointer-events-none absolute top-1/2 left-3 h-[15px] w-[15px] -translate-y-1/2 text-[#94a3b8]"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" strokeLinecap="round" />
          </svg>
          <input
            className="input pl-9"
            placeholder="Rechercher…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="geo-btn inline-flex shrink-0 items-center gap-[0.375rem] rounded-[7px] border border-[#e2e8f0] bg-white px-[0.875rem] py-[0.4375rem] text-[0.8125rem] font-medium whitespace-nowrap text-[#374151]"
          onClick={() => setShowAdvanced((v) => !v)}
        >
          Filtres {showAdvanced ? '▴' : '▾'}
        </button>
        {mode !== 'room' && (
          <select
            className="geo-select cursor-pointer rounded-[7px] border border-[#e2e8f0] bg-white px-[0.625rem] py-[0.4375rem] text-[0.8125rem] text-[#374151] outline-none"
            title="Filtrer par tag"
            value={tag}
            onChange={(e) => setTag(e.target.value)}
          >
            <option value="">Tous les tags</option>
            {tagOptions.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        )}
        <button
          type="button"
          className={`geo-btn inline-flex shrink-0 items-center gap-[0.375rem] rounded-[7px] border border-[#e2e8f0] bg-white px-[0.875rem] py-[0.4375rem] text-[0.8125rem] font-medium whitespace-nowrap text-[#374151] ${geoActive ? 'active' : ''}`}
          onClick={requestGeo}
        >
          {geoLoading ? 'Localisation…' : geoActive ? '● Position active' : '◎ Autour de moi'}
        </button>
        <select
          className="geo-select cursor-pointer rounded-[7px] border border-[#e2e8f0] bg-white px-[0.625rem] py-[0.4375rem] text-[0.8125rem] text-[#374151] outline-none"
          title="Rayon de recherche"
          value={radius}
          onChange={(e) => setRadius(e.target.value)}
        >
          <option value="5">5 km</option>
          <option value="10">10 km</option>
          <option value="25">25 km</option>
          <option value="50">50 km</option>
          <option value="100">100 km</option>
        </select>
      </div>

      {showAdvanced && (
        <div className="filter-bar mb-[0.625rem] flex flex-wrap items-center gap-[0.625rem]">
          <label className="flex items-center gap-1 text-xs text-gray-500">
            Du
            <input
              type="date"
              className="geo-select rounded-[7px] border border-[#e2e8f0] bg-white px-[0.625rem] py-[0.4375rem] text-[0.8125rem] text-[#374151] outline-none"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </label>
          <label className="flex items-center gap-1 text-xs text-gray-500">
            Au
            <input
              type="date"
              className="geo-select rounded-[7px] border border-[#e2e8f0] bg-white px-[0.625rem] py-[0.4375rem] text-[0.8125rem] text-[#374151] outline-none"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </label>
          <label className="flex items-center gap-1 text-xs text-gray-500">
            Prix max (€)
            <input
              type="number"
              min="0"
              className="geo-select w-[80px] rounded-[7px] border border-[#e2e8f0] bg-white px-[0.625rem] py-[0.4375rem] text-[0.8125rem] text-[#374151] outline-none"
              value={priceMax}
              onChange={(e) => setPriceMax(e.target.value)}
            />
          </label>
          <label className="flex items-center gap-1 text-xs text-gray-500">
            Places min
            <input
              type="number"
              min="1"
              className="geo-select w-[70px] rounded-[7px] border border-[#e2e8f0] bg-white px-[0.625rem] py-[0.4375rem] text-[0.8125rem] text-[#374151] outline-none"
              value={seatsMin}
              onChange={(e) => setSeatsMin(e.target.value)}
            />
          </label>
          {mode !== 'room' && (
            <label className="flex cursor-pointer items-center gap-[6px] text-xs text-gray-500">
              <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} /> À
              distance uniquement
            </label>
          )}
          <button
            type="button"
            className="geo-btn inline-flex shrink-0 items-center gap-[0.375rem] rounded-[7px] border border-[#e2e8f0] bg-white px-[0.875rem] py-[0.4375rem] text-[0.8125rem] font-medium whitespace-nowrap text-[#374151]"
            onClick={resetAdvanced}
          >
            Réinitialiser
          </button>
        </div>
      )}

      <div className="mb-3 flex items-center gap-2">
        <button
          className={`geo-btn inline-flex shrink-0 items-center gap-[0.375rem] rounded-[7px] border border-[#e2e8f0] bg-white px-[0.875rem] py-[0.4375rem] text-[0.8125rem] font-medium whitespace-nowrap text-[#374151] ${view === 'list' ? 'active' : ''}`}
          onClick={() => setView('list')}
          title="Vue liste"
        >
          ☰ Liste
        </button>
        <button
          className={`geo-btn inline-flex shrink-0 items-center gap-[0.375rem] rounded-[7px] border border-[#e2e8f0] bg-white px-[0.875rem] py-[0.4375rem] text-[0.8125rem] font-medium whitespace-nowrap text-[#374151] ${view === 'calendar' ? 'active' : ''}`}
          onClick={() => setView('calendar')}
          title="Vue calendrier"
        >
          📅 Calendrier
        </button>
      </div>

      {view === 'list' ? (
        <div className="content-grid">
          {items.map((t) => {
            const isOwner = user && t.provider_id === user.company_id
            return (
              <OfferCard
                key={t.id}
                item={t}
                canBook={!isGuest && !isOwner}
                catalogOwner={isOwner}
                onBook={setBookingTarget}
              />
            )
          })}
          {!visibleCount && <p className="text-sm text-gray-500">{MODE.catalogEmpty}</p>}
        </div>
      ) : (
        <CalendarView items={items} />
      )}

      <BookingModal item={bookingTarget} mode={mode} MODE={MODE} onConfirm={confirmBooking} onClose={() => setBookingTarget(null)} />
    </section>
  )
}
