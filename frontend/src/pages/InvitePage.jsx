import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import AuthLayout from '../components/AuthLayout.jsx'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/AuthContext.jsx'

export default function InvitePage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [companyName, setCompanyName] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')
  const [form, setForm] = useState({ first_name: '', last_name: '', phone: '', password: '' })
  const [error, setError] = useState('')
  const [invalid, setInvalid] = useState(false)

  useEffect(() => {
    if (!token) return
    let cancelled = false
    api(`/auth/invite-info?token=${encodeURIComponent(token)}`)
      .then((info) => {
        if (cancelled) return
        setInviteEmail(info.email || '')
        setCompanyName(info.company_name || '')
      })
      .catch((ex) => {
        if (cancelled) return
        setInvalid(true)
        if (ex.status !== 400) console.warn('Invitation illisible', ex)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const data = await api('/auth/accept-invite', { method: 'POST', body: { token, ...form } })
      login(data)
      navigate('/dashboard')
    } catch (ex) {
      setError(
        ex.data?.message ||
          (ex.data?.messages && JSON.stringify(ex.data.messages)) ||
          'Erreur',
      )
    }
  }

  return (
    <AuthLayout
      subtitle={
        <>
          {companyName && <span className="block font-semibold text-white">{companyName}</span>}
          <span className="mt-2 block">vous invite à rejoindre Avyro</span>
        </>
      }
    >
      <h1 className="text-right text-2xl font-bold text-gray-900">Rejoindre l’équipe</h1>
      {inviteEmail && <p className="mt-1 text-right text-sm text-gray-500">{inviteEmail}</p>}

      {!token || invalid ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Lien d'invitation invalide ou expiré
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <input
              className="input"
              placeholder="Prénom"
              required
              value={form.first_name}
              onChange={(e) => set('first_name', e.target.value)}
            />
            <input
              className="input"
              placeholder="Nom"
              required
              value={form.last_name}
              onChange={(e) => set('last_name', e.target.value)}
            />
          </div>
          <input
            className="input"
            type="tel"
            placeholder="Numéro de téléphone"
            required
            value={form.phone}
            onChange={(e) => set('phone', e.target.value)}
          />
          <input
            className="input"
            type="password"
            placeholder="Mot de passe (8 car. min)"
            required
            value={form.password}
            onChange={(e) => set('password', e.target.value)}
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="btn-primary w-full" type="submit">
            Créer mon compte
          </button>
        </form>
      )}
      <p className="mt-4 text-center text-sm text-gray-600">
        Déjà inscrit ?{' '}
        <Link to="/login" className="font-medium text-avyro-600">
          Se connecter
        </Link>
      </p>
    </AuthLayout>
  )
}
