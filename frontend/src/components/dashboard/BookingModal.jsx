import { useEffect, useState } from 'react'

/** Modale de confirmation de réservation (formation : places + note ; salle : note seule). */
export default function BookingModal({ item, mode, MODE, onConfirm, onClose }) {
  const [seats, setSeats] = useState(1)
  const [note, setNote] = useState('')

  useEffect(() => {
    if (item) {
      setSeats(1)
      setNote('')
    }
  }, [item])

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!item) return null
  const isRoom = mode === 'room'

  function handleSubmit(e) {
    e.preventDefault()
    if (isRoom) {
      onConfirm({ note: note.trim() || null })
    } else {
      const v = parseInt(seats, 10)
      if (v > 0) onConfirm({ seats: v, note: note.trim() || null })
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 [backdrop-filter:blur(2px)]"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-[400px] overflow-hidden rounded-2xl border border-[#e2e8f0] bg-white [box-shadow:0_24px_64px_rgba(15,23,62,0.14),0_4px_16px_rgba(15,23,62,0.06)]">
        <div
          id="book-modal-head"
          className="px-6 py-5 [background:linear-gradient(135deg,#1d4ed8_0%,#3b82f6_100%)]"
        >
          <p className="m-0 mb-[0.2rem] text-[0.6875rem] font-semibold tracking-[0.07em] text-white/65 uppercase">
            Réservation
          </p>
          <h3 className="m-0 text-base font-semibold tracking-[-0.01em] text-white">{item.title}</h3>
        </div>
        <div className="p-6">
          <p className="m-0 mb-4 text-sm leading-[1.5] text-[#64748b]">
            {isRoom
              ? `Salle de ${item.shared_seats} personne(s) — location à l'unité · ${item.price_per_seat} €`
              : MODE.bookPrompt(item.available_seats)}
          </p>
          <form onSubmit={handleSubmit}>
            {!isRoom && (
              <input
                className="input mb-3"
                type="number"
                min="1"
                max={item.available_seats}
                required
                autoFocus
                value={seats}
                onChange={(e) => setSeats(e.target.value)}
              />
            )}
            <textarea
              className="input mb-5 resize-y"
              placeholder="Note pour le provider (optionnel)"
              maxLength={500}
              rows={3}
              autoFocus={isRoom}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button type="button" className="btn-ghost" onClick={onClose}>
                Annuler
              </button>
              <button type="submit" className="btn-primary">
                Confirmer la réservation
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
