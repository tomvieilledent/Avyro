import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth, useRequireAuth } from '../lib/AuthContext.jsx'
import { DashboardProvider, useDashboard } from '../lib/DashboardContext.jsx'
import { clearSession } from '../lib/api.js'
import CatalogPanel from '../components/dashboard/CatalogPanel.jsx'
import MinePanel from '../components/dashboard/MinePanel.jsx'
import BookingsPanel from '../components/dashboard/BookingsPanel.jsx'
import IncomingPanel from '../components/dashboard/IncomingPanel.jsx'
import ReportsPanel from '../components/dashboard/ReportsPanel.jsx'

const ALL_TABS = ['catalog', 'mine', 'bookings', 'incoming', 'reports']
const PANELS = {
  catalog: CatalogPanel,
  mine: MinePanel,
  bookings: BookingsPanel,
  incoming: IncomingPanel,
  reports: ReportsPanel,
}

function DashboardChrome() {
  const { user, logout } = useAuth()
  const { mode, setMode, MODE, isGuest, badgeCount } = useDashboard()
  const [activeTab, setActiveTab] = useState('catalog')
  useRequireAuth({ guest: isGuest })

  const tabs = isGuest ? ['catalog'] : ALL_TABS
  useEffect(() => {
    if (!tabs.includes(activeTab)) setActiveTab('catalog')
  }, [tabs, activeTab])

  useEffect(() => {
    const mark = mode === 'room' ? '/img/mark-room.svg' : '/img/mark-training.svg'
    const icon = document.querySelector('link[rel="icon"]')
    if (icon) icon.href = mark
  }, [mode])

  function handleLogout() {
    clearSession()
    logout()
    location.href = '/login'
  }

  const Panel = PANELS[activeTab]

  return (
    <div className="h-full overflow-hidden bg-[#eef6ff] text-gray-900">
      <div
        id="deco-left"
        aria-hidden="true"
        className="fixed top-[60px] bottom-[36px] left-0 z-0 w-[clamp(120px,12vw,220px)] overflow-hidden"
      >
        <img src="/img/deco-training.svg" alt="" />
      </div>
      <div
        id="deco-right"
        aria-hidden="true"
        className="fixed top-[60px] bottom-[36px] right-0 z-0 w-[clamp(120px,12vw,220px)] overflow-hidden"
      >
        <img src="/img/deco-room-right.svg" alt="" />
      </div>

      <header className="app-header fixed top-0 left-0 z-30 flex h-[60px] w-full items-center justify-between px-6 [background:linear-gradient(135deg,#1d4ed8_0%,#3b82f6_100%)] [box-shadow:0_2px_12px_rgba(29,78,216,0.28)]">
        <div className="flex min-w-0 items-center gap-[0.875rem]">
          <div className="flex shrink-0 items-center gap-2">
            <img src={mode === 'room' ? '/img/mark-room.svg' : '/img/mark-training.svg'} alt="" className="h-7 w-7" />
            <span className="logo-text text-lg font-bold tracking-[-0.02em] text-white">Avyro</span>
          </div>
          <div className="h-sep h-5 w-px shrink-0 bg-white/20" />
          <div className="mode-pill flex rounded-full border border-white/[0.18] bg-white/[0.12] p-[3px]">
            {['training', 'room'].map((m) => (
              <button
                key={m}
                type="button"
                className={`mode-seg cursor-pointer rounded-full border-none bg-transparent px-[14px] py-[4px] text-[0.8rem] leading-[1.4] font-semibold whitespace-nowrap transition-all duration-150 ${mode === m ? 'mode-seg-active' : ''}`}
                onClick={() => setMode(m)}
              >
                {m === 'training' ? 'Training' : 'Room'}
              </button>
            ))}
          </div>
        </div>

        {isGuest ? (
          <div className="flex shrink-0 items-center gap-2">
            <Link
              to="/register"
              className="hbtn inline-flex items-center rounded-[7px] border border-white/40 bg-transparent px-[13px] py-[5px] text-[0.8125rem] font-medium whitespace-nowrap text-white no-underline transition-[background] duration-150 hover:bg-white/[0.12]"
            >
              Créer un compte
            </Link>
            <Link
              to={`/login?next=${mode}`}
              className="hbtn inline-flex items-center rounded-[7px] border border-white/40 bg-transparent px-[13px] py-[5px] text-[0.8125rem] font-medium whitespace-nowrap text-white no-underline transition-[background] duration-150 hover:bg-white/[0.12]"
            >
              Se connecter
            </Link>
          </div>
        ) : (
          <div className="flex shrink-0 items-center gap-2">
            <Link
              to="/profile"
              id="who"
              className="hidden max-w-[180px] overflow-hidden text-sm text-ellipsis whitespace-nowrap text-white/75 no-underline transition-colors duration-100 hover:text-white sm:inline"
            >
              {user?.full_name}
            </Link>
            <Link
              to="/profile"
              className="hbtn inline-flex items-center rounded-[7px] border border-white/40 bg-transparent px-[13px] py-[5px] text-[0.8125rem] font-medium whitespace-nowrap text-white no-underline transition-[background] duration-150 hover:bg-white/[0.12]"
            >
              Profil
            </Link>
            <button
              onClick={handleLogout}
              className="hbtn inline-flex items-center rounded-[7px] border border-white/40 bg-transparent px-[13px] py-[5px] text-[0.8125rem] font-medium whitespace-nowrap text-white transition-[background] duration-150 hover:bg-white/[0.12]"
            >
              Déconnexion
            </button>
          </div>
        )}
      </header>

      <main className="fixed top-[60px] left-0 h-[calc(100vh-96px)] w-full overflow-y-auto">
        <div className="mx-auto max-w-[1100px] px-6 pb-10">
          <div className="tab-bar sticky top-0 z-20 bg-[#eef6ff] pt-6">
            <div className="tab-nav flex overflow-x-auto border-b-2 border-[#bfdbfe]" role="tablist">
              {tabs.map((name) => (
                <button
                  key={name}
                  role="tab"
                  className={`tab mb-[-2px] shrink-0 border-none border-b-2 border-transparent bg-transparent px-[18px] py-[10px] text-sm font-medium whitespace-nowrap text-[#64748b] outline-none transition-colors duration-150 ${activeTab === name ? 'tab-active' : ''}`}
                  onClick={() => setActiveTab(name)}
                >
                  {MODE.tabs[name]}
                  {name === 'incoming' && badgeCount > 0 && (
                    <span className="ml-1 rounded-full bg-red-500 px-[6px] py-[1px] align-middle text-[0.65rem] font-bold text-white">
                      {badgeCount}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <Panel />
        </div>
      </main>

      <footer className="app-footer fixed bottom-0 left-0 z-30 flex h-9 w-full items-center justify-center border-t border-white/[0.08] text-xs font-normal tracking-[0.01em] text-white/55 [background:linear-gradient(135deg,#1d4ed8_0%,#3b82f6_100%)]">
        <p className="flex-1 text-center">{MODE.desc}</p>
        <span className="absolute right-8">
          © 2026 AVYRO.{' '}
          <a href="/privacy" className="text-inherit underline decoration-dotted opacity-70">
            Confidentialité
          </a>
        </span>
      </footer>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <DashboardProvider>
      <DashboardChrome />
    </DashboardProvider>
  )
}
