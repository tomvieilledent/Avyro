import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api.js'
import { fmtDate } from '../lib/format.js'

function OfferRow({ item }) {
  return (
    <div className="card flex items-center justify-between gap-3">
      <div className="min-w-0 flex-1">
        <h3 className="font-semibold">{item.title}</h3>
        <p className="mt-0.5 text-sm text-gray-500">
          {fmtDate(item.starts_at)} · {item.is_remote ? 'À distance' : item.location || '—'}
        </p>
        <p className="mt-1 text-sm text-gray-600">
          {item.available_seats} place(s) · {item.price_per_seat} €/place
        </p>
      </div>
      <Link to="/dashboard" className="btn-primary shrink-0 px-[14px] py-[6px] text-[0.8125rem]">
        Réserver
      </Link>
    </div>
  )
}

export default function CompanyPage() {
  const [searchParams] = useSearchParams()
  const companyId = searchParams.get('id')
  const [data, setData] = useState(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!companyId) return
    api(`/companies/${companyId}/offerings`)
      .then(setData)
      .catch(() => setNotFound(true))
  }, [companyId])

  if (!companyId) return <p className="p-8 text-sm text-gray-500">Fiche entreprise introuvable.</p>

  return (
    <div className="min-h-screen bg-[#f8fafc]">
      <header className="fixed top-0 left-0 z-30 flex h-[60px] w-full items-center justify-between bg-[#1e3a8a] px-6 [box-shadow:0_2px_12px_rgba(15,23,62,0.22)]">
        <Link
          to="/dashboard"
          className="flex items-center gap-2 text-lg font-bold tracking-[-0.02em] text-white no-underline"
        >
          <img src="/img/mark-training.svg" alt="" className="h-7 w-7" />
          Avyro
        </Link>
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault()
            history.back()
          }}
          className="inline-flex items-center rounded-[7px] border border-white/40 bg-transparent px-[13px] py-[5px] text-[0.8125rem] font-medium text-white no-underline transition-[background] duration-150 hover:bg-white/[0.12]"
        >
          ← Retour
        </a>
      </header>

      <main className="mx-auto max-w-[900px] px-6 pt-20 pb-12">
        {notFound && <p className="text-sm text-gray-500">Entreprise introuvable.</p>}
        {!notFound && !data && <p className="text-sm text-gray-500">Chargement…</p>}
        {data && (
          <div>
            <div className="card mb-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{data.company.name}</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    {data.company.kind === 'pro' ? 'Entreprise' : 'Particulier'}
                  </p>
                </div>
                {data.company.contact_email && (
                  <a
                    href={`mailto:${data.company.contact_email}`}
                    className="inline-flex items-center rounded-[7px] border border-[#1d4ed8] bg-[#eff6ff] px-[13px] py-[5px] text-[0.8125rem] font-medium text-avyro-600 no-underline"
                  >
                    Contacter
                  </a>
                )}
              </div>
            </div>

            <h2 className="mt-6 mb-3 text-lg font-semibold">Formations disponibles</h2>
            <div className="content-list">
              {data.trainings.map((t) => (
                <OfferRow key={t.id} item={t} />
              ))}
            </div>
            {!data.trainings.length && <p className="text-sm text-gray-500">Aucune formation disponible.</p>}

            <h2 className="mt-6 mb-3 text-lg font-semibold">Salles disponibles</h2>
            <div className="content-list">
              {data.rooms.map((r) => (
                <OfferRow key={r.id} item={r} />
              ))}
            </div>
            {!data.rooms.length && <p className="text-sm text-gray-500">Aucune salle disponible.</p>}
          </div>
        )}
      </main>
    </div>
  )
}
