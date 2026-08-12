import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import AuthLayout from '../components/AuthLayout.jsx'
import { api } from '../lib/api.js'
import { useAuth } from '../lib/AuthContext.jsx'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      const data = await api('/auth/login', { method: 'POST', body: form })
      login(data)
      const next = searchParams.get('next')
      if (next === 'room' || next === 'training') localStorage.setItem('avyro_mode', next)
      navigate('/dashboard')
    } catch (ex) {
      setError(ex.data?.message || 'Identifiants invalides')
    }
  }

  return (
    <AuthLayout subtitle={<>La plateforme de mutualisation<br />entre entreprises</>}>
      <h1 className="text-right text-2xl font-bold text-gray-900">Connexion</h1>
      <p className="mt-1 text-right text-sm text-gray-500">Bienvenue sur Avyro</p>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <input
          className="input"
          type="email"
          placeholder="Email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          className="input"
          type="password"
          placeholder="Mot de passe"
          required
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full" type="submit">
          Se connecter
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-gray-600">
        Pas de compte ?{' '}
        <Link to="/register" className="font-medium text-avyro-600">
          Créer un compte
        </Link>
      </p>
    </AuthLayout>
  )
}
