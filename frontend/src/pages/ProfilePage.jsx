import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errText, getToken } from '../lib/api.js'
import { useAuth, useRequireAuth } from '../lib/AuthContext.jsx'

function Flash({ text, ok }) {
  if (!text) return null
  return <p className={`text-sm sm:col-span-2 ${ok ? 'text-green-600' : 'text-red-600'}`}>{text}</p>
}

export default function ProfilePage() {
  useRequireAuth()
  const { refreshUser } = useAuth()
  const [isAdmin, setIsAdmin] = useState(false)
  const [userForm, setUserForm] = useState(null)
  const [companyForm, setCompanyForm] = useState(null)
  const [inviteForm, setInviteForm] = useState({ email: '', role: 'member' })
  const [userMsg, setUserMsg] = useState(null)
  const [companyMsg, setCompanyMsg] = useState(null)
  const [inviteMsg, setInviteMsg] = useState(null)
  const [rgpdMsg, setRgpdMsg] = useState(null)
  const mode = localStorage.getItem('avyro_mode') === 'room' ? 'room' : 'training'

  useEffect(() => {
    document.body.classList.toggle('mode-room', mode === 'room')
  }, [mode])

  useEffect(() => {
    ;(async () => {
      const me = await api('/auth/me')
      setUserForm({
        first_name: me.first_name,
        last_name: me.last_name,
        email: me.email,
        phone: me.phone || '',
        password: '',
      })
      if (me.role !== 'admin') return
      setIsAdmin(true)
      const company = await api('/companies/me')
      setCompanyForm({
        name: company.name,
        kind: company.kind,
        siret: company.siret || '',
        contact_email: company.contact_email || '',
      })
    })()
  }, [])

  async function submitUser(e) {
    e.preventDefault()
    const body = {
      first_name: userForm.first_name,
      last_name: userForm.last_name,
      email: userForm.email,
      phone: userForm.phone,
    }
    if (userForm.password) body.password = userForm.password
    try {
      const updated = await api('/auth/me', { method: 'PATCH', body })
      refreshUser(updated)
      setUserForm((f) => ({ ...f, password: '' }))
      setUserMsg({ ok: true, text: 'Profil mis à jour.' })
    } catch (ex) {
      setUserMsg({ ok: false, text: errText(ex) })
    }
  }

  async function submitInvite(e) {
    e.preventDefault()
    try {
      await api('/companies/me/invite', { method: 'POST', body: inviteForm })
      setInviteMsg({ ok: true, text: `Invitation envoyée à ${inviteForm.email}.` })
      setInviteForm({ email: '', role: 'member' })
    } catch (ex) {
      setInviteMsg({ ok: false, text: errText(ex) })
    }
  }

  async function submitCompany(e) {
    e.preventDefault()
    try {
      await api('/companies/me', {
        method: 'PATCH',
        body: {
          name: companyForm.name,
          kind: companyForm.kind,
          siret: companyForm.siret || null,
          contact_email: companyForm.contact_email || null,
        },
      })
      setCompanyMsg({ ok: true, text: 'Structure mise à jour.' })
    } catch (ex) {
      setCompanyMsg({ ok: false, text: errText(ex) })
    }
  }

  async function exportData(e) {
    e.preventDefault()
    try {
      const token = getToken()
      const res = await fetch('/api/auth/me/export', { headers: { Authorization: `Bearer ${token}` } })
      const data = await res.json()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'avyro_mes_donnees.json'
      a.click()
      URL.revokeObjectURL(url)
    } catch (ex) {
      setRgpdMsg({ ok: false, text: errText(ex) })
    }
  }

  async function deleteAccount() {
    if (!confirm('Supprimer définitivement votre compte ? Cette action est irréversible.')) return
    if (!confirm('Confirmez-vous la suppression de toutes vos données personnelles ?')) return
    try {
      await api('/auth/me', { method: 'DELETE' })
      localStorage.removeItem('avyro_token')
      localStorage.removeItem('avyro_refresh')
      localStorage.removeItem('avyro_user')
      location.href = '/'
    } catch (ex) {
      setRgpdMsg({ ok: false, text: errText(ex) })
    }
  }

  if (!userForm) return null

  return (
    <div className="h-full overflow-hidden text-gray-900">
      <header className="app-header fixed top-0 left-0 z-30 flex h-[60px] w-full items-center justify-between bg-[#1e3a8a] px-8 [box-shadow:0_2px_8px_rgba(15,23,62,0.25)]">
        <Link
          to="/dashboard"
          className="logo-link flex items-center gap-[9px] text-lg font-bold tracking-[-0.02em] text-white no-underline"
        >
          <img src="/img/mark-training.svg" alt="" className="h-7 w-7" />
          Avyro
        </Link>
        <Link
          to="/dashboard"
          className="hbtn inline-flex items-center rounded-[6px] border border-white/40 bg-transparent px-[13px] py-[5px] text-[0.8125rem] font-medium text-white no-underline transition-[background] duration-150 hover:bg-white/[0.12]"
        >
          ← Tableau de bord
        </Link>
      </header>

      <main className="fixed top-[60px] left-0 h-[calc(100vh-96px)] w-full overflow-y-auto">
        <div className="mx-auto max-w-[720px] p-8">
          <h1 className="mb-6 text-2xl font-bold">Mon profil</h1>

          <section className="card mb-6">
            <h2 className="text-lg font-semibold">Compte</h2>
            <form onSubmit={submitUser} className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label className="text-xs text-gray-500">
                Prénom <span className="text-red-500">*</span>
                <input
                  className="input"
                  required
                  value={userForm.first_name}
                  onChange={(e) => setUserForm({ ...userForm, first_name: e.target.value })}
                />
              </label>
              <label className="text-xs text-gray-500">
                Nom <span className="text-red-500">*</span>
                <input
                  className="input"
                  required
                  value={userForm.last_name}
                  onChange={(e) => setUserForm({ ...userForm, last_name: e.target.value })}
                />
              </label>
              <label className="text-xs text-gray-500 sm:col-span-2">
                Email <span className="text-red-500">*</span>
                <input
                  className="input"
                  type="email"
                  required
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                />
              </label>
              <label className="text-xs text-gray-500 sm:col-span-2">
                Téléphone <span className="text-red-500">*</span>
                <input
                  className="input"
                  type="tel"
                  required
                  value={userForm.phone}
                  onChange={(e) => setUserForm({ ...userForm, phone: e.target.value })}
                />
              </label>
              <label className="text-xs text-gray-500 sm:col-span-2">
                Nouveau mot de passe (laisser vide pour ne pas changer)
                <input
                  className="input"
                  type="password"
                  minLength={8}
                  placeholder="••••••••"
                  value={userForm.password}
                  onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                />
              </label>
              <Flash text={userMsg?.text} ok={userMsg?.ok} />
              <div className="sm:col-span-2">
                <button className="btn-primary" type="submit">
                  Enregistrer
                </button>
              </div>
            </form>
          </section>

          {isAdmin && (
            <section className="card mb-6">
              <h2 className="text-lg font-semibold">Inviter un membre</h2>
              <p className="mt-1 text-sm text-gray-500">
                Envoyez un lien d’invitation par email (valable 7 jours).
              </p>
              <form onSubmit={submitInvite} className="mt-4 flex gap-2">
                <input
                  className="input flex-1"
                  type="email"
                  placeholder="Email du membre à inviter"
                  required
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                />
                <select
                  className="input w-auto shrink-0"
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                >
                  <option value="member">Membre</option>
                  <option value="admin">Admin</option>
                </select>
                <button className="btn-primary shrink-0" type="submit">
                  Inviter
                </button>
              </form>
              {inviteMsg && (
                <p className={`mt-2 text-sm ${inviteMsg.ok ? 'text-green-600' : 'text-red-600'}`}>
                  {inviteMsg.text}
                </p>
              )}
            </section>
          )}

          {isAdmin && companyForm && (
            <section className="card">
              <h2 className="text-lg font-semibold">Ma structure</h2>
              <form onSubmit={submitCompany} className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                <label className="text-xs text-gray-500 sm:col-span-2">
                  Nom <span className="text-red-500">*</span>
                  <input
                    className="input"
                    required
                    value={companyForm.name}
                    onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                  />
                </label>
                <label className="text-xs text-gray-500">
                  Type
                  <select
                    className="input"
                    value={companyForm.kind}
                    onChange={(e) => setCompanyForm({ ...companyForm, kind: e.target.value })}
                  >
                    <option value="pro">Entreprise</option>
                    <option value="private">Particulier</option>
                  </select>
                </label>
                <label className="text-xs text-gray-500">
                  SIRET
                  <input
                    className="input"
                    value={companyForm.siret}
                    onChange={(e) => setCompanyForm({ ...companyForm, siret: e.target.value })}
                  />
                </label>
                <label className="text-xs text-gray-500 sm:col-span-2">
                  Email de contact
                  <input
                    className="input"
                    type="email"
                    value={companyForm.contact_email}
                    onChange={(e) => setCompanyForm({ ...companyForm, contact_email: e.target.value })}
                  />
                </label>
                <Flash text={companyMsg?.text} ok={companyMsg?.ok} />
                <div className="sm:col-span-2">
                  <button className="btn-primary" type="submit">
                    Enregistrer
                  </button>
                </div>
              </form>
            </section>
          )}

          <section className="card mt-6 border-[#fca5a5]">
            <h2 className="text-lg font-semibold">Données personnelles (RGPD)</h2>
            <p className="mt-1 text-sm text-gray-500">
              Conformément au Règlement Général sur la Protection des Données.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <a
                href="#"
                onClick={exportData}
                className="hbtn inline-flex items-center rounded-[6px] border border-avyro-600 bg-[#eff6ff] px-[13px] py-[5px] text-[0.8125rem] font-medium text-avyro-600 no-underline"
              >
                ⬇ Exporter mes données
              </a>
              <button
                onClick={deleteAccount}
                className="hbtn inline-flex items-center rounded-[6px] border border-red-500 bg-transparent px-[13px] py-[5px] text-[0.8125rem] font-medium text-red-500"
              >
                Supprimer mon compte
              </button>
            </div>
            {rgpdMsg && (
              <p className={`mt-2 text-sm ${rgpdMsg.ok ? 'text-green-600' : 'text-red-600'}`}>{rgpdMsg.text}</p>
            )}
          </section>
        </div>
      </main>

      <footer className="app-footer fixed bottom-0 left-0 z-30 flex h-9 w-full items-center justify-center border-t border-white/[0.08] bg-[#1e3a8a] text-xs font-normal tracking-[0.01em] text-white/55">
        <p className="flex-1 text-center">
          {mode === 'room'
            ? 'Avyro Room — mutualisez vos salles de réunion : proposez vos salles à des entreprises externes.'
            : 'Avyro Training — mutualisez vos formations : proposez vos places restantes à d’autres entreprises.'}
        </p>
        <span className="absolute right-8">© 2026 AVYRO. Tous droits réservés.</span>
      </footer>
    </div>
  )
}
