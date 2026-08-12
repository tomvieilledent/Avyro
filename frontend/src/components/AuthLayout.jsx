import { Link } from 'react-router-dom'
import { useDiagonalSplit } from '../lib/useDiagonalSplit.js'

/**
 * Écran divisé en diagonale : branding Avyro à gauche, contenu (formulaire) à
 * droite. Utilisé par les pages Connexion, Inscription et Invitation.
 */
export default function AuthLayout({ subtitle, children }) {
  const { viewBox, leftPoints, rightPoints, line } = useDiagonalSplit(63)

  return (
    <div className="relative flex h-screen overflow-hidden">
      <svg className="fixed inset-0 z-0 h-screen w-screen" viewBox={viewBox}>
        <defs>
          <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1D4ED8" />
            <stop offset="100%" stopColor="#3B82F6" />
          </linearGradient>
        </defs>
        <polygon points={leftPoints} fill="url(#blueGrad)" />
        <polygon points={rightPoints} fill="#f8fafc" />
        <line
          x1={line.x1}
          y1={line.y1}
          x2={line.x2}
          y2={line.y2}
          stroke="white"
          strokeWidth="3"
          strokeOpacity="0.45"
          vectorEffect="non-scaling-stroke"
        />
      </svg>

      <div className="relative z-10 flex flex-1 flex-col items-center justify-center py-12 pr-[4vw] pl-[8vw]">
        <Link to="/">
          <div className="w-[220px] rounded-2xl bg-white p-4 shadow-xl">
            <img src="/img/logo-avyro.svg" alt="Avyro" className="w-full" />
          </div>
        </Link>
        <p className="mt-6 max-w-xs text-center text-sm text-white/75">{subtitle}</p>
      </div>

      <div className="relative z-10 flex h-screen flex-1 items-center justify-end pr-[5vw]">
        <div className="w-full max-w-sm">{children}</div>
      </div>

      <span className="fixed right-8 bottom-4 z-10 text-[0.7rem] tracking-[0.01em] text-[rgba(30,58,138,0.4)]">
        © 2026 AVYRO. Tous droits réservés.
      </span>
    </div>
  )
}
