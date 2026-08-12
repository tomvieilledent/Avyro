import { useState } from 'react'

const WEEKDAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

/** Vue calendrier mensuelle du catalogue (points bleus = offres du jour). */
export default function CalendarView({ items }) {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth())
  const [selectedDay, setSelectedDay] = useState(null)

  function changeMonth(delta) {
    let m = month + delta
    let y = year
    if (m < 0) {
      m = 11
      y -= 1
    } else if (m > 11) {
      m = 0
      y += 1
    }
    setMonth(m)
    setYear(y)
    setSelectedDay(null)
  }

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const monthName = new Date(year, month, 1).toLocaleString('fr-FR', { month: 'long', year: 'numeric' })

  const itemsByDay = {}
  items.forEach((t) => {
    const d = new Date(t.starts_at)
    if (d.getFullYear() === year && d.getMonth() === month) {
      const key = d.getDate()
      if (!itemsByDay[key]) itemsByDay[key] = []
      itemsByDay[key].push(t)
    }
  })

  const startBlanks = firstDay === 0 ? 6 : firstDay - 1
  const cells = []
  for (let i = 0; i < startBlanks; i++) cells.push(null)
  for (let day = 1; day <= daysInMonth; day++) cells.push(day)

  const dayItems = selectedDay ? itemsByDay[selectedDay] || [] : []

  return (
    <div className="rounded-xl border border-[#e2e8f0] bg-white p-4 [box-shadow:0_1px_4px_rgba(0,0,0,0.06)]">
      <div className="mb-3 flex items-center justify-between">
        <button className="geo-btn rounded-[7px] border border-[#e2e8f0] px-3 py-1.5 text-sm" onClick={() => changeMonth(-1)}>
          ‹
        </button>
        <span className="font-semibold capitalize">{monthName}</span>
        <button className="geo-btn rounded-[7px] border border-[#e2e8f0] px-3 py-1.5 text-sm" onClick={() => changeMonth(1)}>
          ›
        </button>
      </div>
      <div className="grid grid-cols-7 border-t border-l border-[#e2e8f0] text-center text-xs">
        {WEEKDAYS.map((d) => (
          <div key={d} className="border-r border-b border-[#e2e8f0] bg-[#f8fafc] py-1.5 font-semibold text-[#64748b]">
            {d}
          </div>
        ))}
        {cells.map((day, i) => {
          if (day === null) return <div key={i} className="border-r border-b border-[#e2e8f0] bg-[#fafafa]" />
          const dayEvents = itemsByDay[day] || []
          const isToday = now.getDate() === day && now.getMonth() === month && now.getFullYear() === year
          const bg = isToday ? '#eff6ff' : dayEvents.length ? '#f0fdf4' : '#fff'
          return (
            <div
              key={i}
              className="min-h-[52px] border-r border-b border-[#e2e8f0] p-1.5 transition-colors"
              style={{ background: bg, cursor: dayEvents.length ? 'pointer' : 'default' }}
              onClick={() => dayEvents.length && setSelectedDay(day)}
            >
              <div className="text-[0.8125rem]" style={{ fontWeight: isToday ? 700 : 400, color: isToday ? '#1d4ed8' : '#1e293b' }}>
                {day}
              </div>
              <div className="mt-1 flex flex-wrap justify-center gap-0.5">
                {dayEvents.slice(0, 3).map((_, idx) => (
                  <span key={idx} className="inline-block h-1.5 w-1.5 rounded-full bg-[#1d4ed8]" />
                ))}
                {dayEvents.length > 3 && <span className="text-[0.6rem] text-[#64748b]">+{dayEvents.length - 3}</span>}
              </div>
            </div>
          )
        })}
      </div>
      {selectedDay && (
        <div className="mt-4">
          <p className="mb-2 font-semibold">
            {selectedDay} {new Date(year, month, selectedDay).toLocaleString('fr-FR', { month: 'long' })}
          </p>
          {dayItems.map((t) => (
            <div key={t.id} className="card mb-2 p-3">
              <b>{t.title}</b> — {t.provider_name}
              <br />
              <span className="text-sm text-gray-500">
                {t.available_seats} place(s) · {t.price_per_seat} €
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
