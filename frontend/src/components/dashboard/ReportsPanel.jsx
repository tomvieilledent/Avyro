import { useCallback, useEffect, useState } from 'react'
import { api } from '../../lib/api.js'
import { useDashboard } from '../../lib/DashboardContext.jsx'
import { fmtDate } from '../../lib/format.js'

function csvHref(report) {
  const rows = [['Structure', 'Places', 'Contact', 'Email']].concat(
    (report.attendees || []).map((a) => [a.company_name, a.seats, a.contact_name, a.contact_email]),
  )
  const content = rows
    .map((row) => row.map((v) => `"${String(v || '').replace(/"/g, '""')}"`).join(','))
    .join('\n')
  return `data:text/csv;charset=utf-8,${encodeURIComponent(content)}`
}

function safeName(report) {
  return (report.training_title || report.room_title || 'rapport').replace(/[^a-z0-9]/gi, '_')
}

export default function ReportsPanel() {
  const { apiBase } = useDashboard()
  const [reports, setReports] = useState([])

  const load = useCallback(async () => {
    const list = await api(`${apiBase}/reports`)
    setReports(list)
  }, [apiBase])

  useEffect(() => {
    load()
  }, [load])

  return (
    <section className="pt-7">
      <div className="panel-hd mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2>Comptes rendus</h2>
          <p>Inscrits confirmés — un email de rappel est envoyé 1 jour ouvré avant le début.</p>
        </div>
      </div>
      <div className="content-grid">
        {reports.map((r) => (
          <div key={r.training_id || r.room_id} className="card">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-semibold">{r.training_title || r.room_title}</h3>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500">Début : {fmtDate(r.starts_at)}</span>
                <a href={csvHref(r)} download={`${safeName(r)}.csv`} className="btn-ghost px-[10px] py-[4px] text-xs">
                  ⬇ CSV
                </a>
              </div>
            </div>
            <p className="mt-1 text-sm text-gray-600">
              <b>{r.total_seats}</b> inscrit(s) confirmé(s)
            </p>
            {r.attendees?.length ? (
              <div className="mt-3 overflow-x-auto">
                <table className="r-table">
                  <thead>
                    <tr>
                      <th>Structure</th>
                      <th>Places</th>
                      <th>Contact</th>
                      <th>Email</th>
                    </tr>
                  </thead>
                  <tbody>
                    {r.attendees.map((a, i) => (
                      <tr key={i}>
                        <td>{a.company_name}</td>
                        <td>{a.seats}</td>
                        <td>{a.contact_name}</td>
                        <td>{a.contact_email}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-2 text-sm text-gray-500">Aucun inscrit confirmé.</p>
            )}
          </div>
        ))}
        {!reports.length && <p className="text-sm text-gray-500">Aucun compte rendu pour le moment.</p>}
      </div>
    </section>
  )
}
