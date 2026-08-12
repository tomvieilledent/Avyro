import { Navigate, Route, Routes } from 'react-router-dom'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import InvitePage from './pages/InvitePage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import CompanyPage from './pages/CompanyPage.jsx'
import PrivacyPage from './pages/PrivacyPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/invite" element={<InvitePage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/profile" element={<ProfilePage />} />
      <Route path="/company" element={<CompanyPage />} />
      <Route path="/privacy" element={<PrivacyPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
