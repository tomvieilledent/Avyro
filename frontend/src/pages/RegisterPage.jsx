import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthLayout from '../components/AuthLayout.jsx'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/AuthContext.jsx'

const INITIAL = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  company_name: '',
  tags: '',
  password: '',
  consent: false,
}

export default function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(INITIAL)
  const [error, setError] = useState('')

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const body = {
        ...form,
        tags: form.tags
          ? form.tags.split(',').map((t) => t.trim()).filter(Boolean)
          : undefined,
      }
      delete body.consent
      const data = await api('/auth/register', { method: 'POST', body })
      login(data)
      navigate('/dashboard')
    } catch (ex) {
      const msgs = ex.data?.messages
      setError(
        msgs
          ? Object.entries(msgs)
              .map(([k, v]) => `${k} : ${v}`)
              .join(' | ')
          : ex.data?.message || 'Erreur lors de l’inscription',
      )
    }
  }

  return (
    <AuthLayout subtitle={<>La plateforme de mutualisation<br />entre entreprises</>}>
      <h1 className="text-right text-2xl font-bold text-gray-900">Créer un compte</h1>
      <p className="mt-1 text-right text-sm text-gray-500">Rejoignez Avyro</p>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            <span>
              Prénom <span className="text-red-500">*</span>
            </span>
            <input
              className="input"
              placeholder="Prénom"
              required
              value={form.first_name}
              onChange={(e) => set('first_name', e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-xs text-gray-500">
            <span>
              Nom <span className="text-red-500">*</span>
            </span>
            <input
              className="input"
              placeholder="Nom"
              required
              value={form.last_name}
              onChange={(e) => set('last_name', e.target.value)}
            />
          </label>
        </div>
        <label className="flex flex-col gap-1 text-xs text-gray-500">
          <span>
            Email <span className="text-red-500">*</span>
          </span>
          <input
            className="input"
            type="email"
            placeholder="Email"
            required
            value={form.email}
            onChange={(e) => set('email', e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-gray-500">
          <span>
            Téléphone <span className="text-red-500">*</span>
          </span>
          <input
            className="input"
            type="tel"
            placeholder="Numéro de téléphone"
            required
            value={form.phone}
            onChange={(e) => set('phone', e.target.value)}
          />
        </label>
        <input
          className="input"
          placeholder="Entreprise (optionnel)"
          value={form.company_name}
          onChange={(e) => set('company_name', e.target.value)}
        />
        <input
          className="input"
          placeholder="Tags de votre entreprise, séparés par des virgules (ex: IT, RH, sécurité)"
          value={form.tags}
          onChange={(e) => set('tags', e.target.value)}
        />
        <label className="flex flex-col gap-1 text-xs text-gray-500">
          <span>
            Mot de passe <span className="text-red-500">*</span>
          </span>
          <input
            className="input"
            type="password"
            placeholder="8 caractères minimum"
            required
            value={form.password}
            onChange={(e) => set('password', e.target.value)}
          />
        </label>
        <label className="flex items-start gap-2 text-xs text-gray-600">
          <input
            type="checkbox"
            required
            className="mt-0.5 shrink-0"
            checked={form.consent}
            onChange={(e) => set('consent', e.target.checked)}
          />
          <span>
            J’accepte la{' '}
            <a href="/privacy" target="_blank" rel="noreferrer" className="text-avyro-600 underline">
              politique de confidentialité
            </a>{' '}
            et le traitement de mes données personnelles conformément au RGPD.{' '}
            <span className="text-red-500">*</span>
          </span>
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" type="submit">
          Créer mon compte
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-gray-600">
        Déjà inscrit ?{' '}
        <Link to="/login" className="font-medium text-avyro-600">
          Se connecter
        </Link>
      </p>
    </AuthLayout>
  )
}
