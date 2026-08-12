import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useDiagonalSplit } from '../lib/useDiagonalSplit.js'
import { getToken } from '../lib/api.js'

export default function LandingPage() {
  const { viewBox, leftPoints, rightPoints } = useDiagonalSplit(62)
  const navigate = useNavigate()
  const [grayLeft, setGrayLeft] = useState(false)
  const [grayRight, setGrayRight] = useState(false)

  function openMode(mode) {
    if (getToken()) {
      localStorage.setItem('avyro_mode', mode)
      navigate('/dashboard')
    } else {
      navigate(`/dashboard?mode=${mode}&guest=1`)
    }
  }

  return (
    <div className="relative flex h-screen flex-col overflow-hidden">
      <svg className="fixed inset-0 z-0 h-screen w-screen" viewBox={viewBox}>
        <defs>
          <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1D4ED8" />
            <stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>
          <linearGradient id="roomGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#F8FAFC" />
            <stop offset="100%" stopColor="#CBD5E1" />
          </linearGradient>
        </defs>
        <polygon
          points={leftPoints}
          fill="url(#blueGrad)"
          className="transition-[filter] duration-[400ms]"
          style={{ filter: grayLeft ? 'grayscale(1)' : '' }}
        />
        <polygon
          points={rightPoints}
          fill="url(#roomGrad)"
          className="transition-[filter] duration-[400ms]"
          style={{ filter: grayRight ? 'grayscale(1) brightness(0.65)' : '' }}
        />
      </svg>

      <header className="fixed top-0 left-0 flex h-[15vh] w-full flex-col items-center justify-center text-center">
        <span className="text-3xl font-extrabold tracking-tight text-white drop-shadow-lg">Avyro</span>
        <p className="mt-1 text-xs font-medium text-white/90 drop-shadow">
          La plateforme de mutualisation entre entreprises
        </p>
      </header>

      <main className="fixed top-[10vh] left-0 z-20 flex h-[80vh] w-full flex-col items-center justify-center">
        <div className="relative flex w-full flex-row items-center gap-[3vw] px-[3vw]">
          <div
            className="shrink-0 basis-[15vw] cursor-pointer transition-[opacity,filter] duration-[400ms]"
            style={{ filter: grayLeft ? 'grayscale(1)' : '' }}
            onClick={() => openMode('training')}
            onMouseEnter={() => setGrayRight(true)}
            onMouseLeave={() => setGrayRight(false)}
          >
            <div className="w-full rounded-2xl bg-white p-4 shadow-xl">
              <img src="/img/logo-training2.svg" alt="Avyro Training" className="w-full" />
            </div>
          </div>

          <img
            src="/img/fond.jpeg"
            alt=""
            className="h-auto w-full min-w-0 flex-1 rounded-[10px] shadow-2xl"
          />

          <div
            className="shrink-0 basis-[15vw] cursor-pointer transition-[opacity,filter] duration-[400ms]"
            style={{ filter: grayRight ? 'grayscale(1) brightness(0.65)' : '' }}
            onClick={() => openMode('room')}
            onMouseEnter={() => setGrayLeft(true)}
            onMouseLeave={() => setGrayLeft(false)}
          >
            <div className="w-full rounded-2xl p-4 shadow-xl [background:linear-gradient(to_bottom,#1d4ed8,#3b82f6)]">
              <img src="/img/logo-room2.svg" alt="Avyro Room" className="w-full" />
            </div>
          </div>

          <div
            className="absolute top-[calc(100%+0.75rem)] left-[3vw] flex w-[22.5vw] flex-col gap-3 transition-[filter] duration-[400ms]"
            style={{ filter: grayLeft ? 'grayscale(1)' : '' }}
          >
            <div className="flex w-fit items-center gap-2 rounded-full bg-white/20 px-3 py-1.5">
              <span className="text-xs font-semibold text-white">Formations</span>
            </div>
            <p className="w-fit text-sm text-white/90">
              <span className="block whitespace-nowrap">Une place libre sur une formation ?</span>
              Proposez-la à d’autres entreprises et <strong className="text-white">partagez les coûts</strong>.
              Remplissez vos sessions, réduisez la facture.
            </p>
          </div>

          <div
            className="absolute top-[calc(100%+0.75rem)] right-[3vw] flex w-[22.5vw] flex-col items-end gap-3 transition-[filter] duration-[400ms]"
            style={{ filter: grayRight ? 'grayscale(1) brightness(0.65)' : '' }}
          >
            <div className="flex w-fit items-center gap-2 rounded-full bg-gray-200 px-3 py-1.5">
              <span className="text-xs font-semibold text-gray-700">Salles de réunion</span>
            </div>
            <p className="w-fit text-right text-sm text-[#1e3a8a]">
              <span className="block whitespace-nowrap">Une salle de réunion inoccupée ?</span>
              Mettez-la à disposition d’entreprises externes et
              <br />
              <strong className="text-[#1e3a8a]">rentabilisez vos espaces</strong>.
            </p>
          </div>
        </div>
      </main>

      <footer className="fixed bottom-0 left-0 flex h-[10vh] w-full flex-col items-center justify-center gap-3 bg-transparent px-6">
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/login"
            className="rounded-lg bg-white px-6 py-2.5 text-sm font-semibold text-gray-900 shadow-lg transition hover:bg-gray-100"
          >
            Se connecter
          </Link>
          <Link
            to="/register"
            className="rounded-lg bg-white px-6 py-2.5 text-sm font-semibold text-gray-900 shadow-lg transition hover:bg-gray-100"
          >
            Créer un compte
          </Link>
        </div>
        <p className="mt-2 text-center text-xs text-[#1e3a8a]">
          Un seul compte pour Avyro Training et Avyro Room.
        </p>
        <span className="absolute right-8 bottom-0 flex h-[30%] items-center text-[0.7rem] tracking-[0.01em] text-[rgba(30,58,138,0.45)]">
          © 2026 AVYRO. Tous droits réservés.
        </span>
      </footer>
    </div>
  )
}
