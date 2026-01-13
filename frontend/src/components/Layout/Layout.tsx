import { ReactNode, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ru' ? 'en' : 'ru'
    i18n.changeLanguage(newLang)
  }

  const menuItems = [
    { path: '/', label: t('nav.dashboard'), icon: '📊' },
    { path: '/threats', label: t('nav.threats'), icon: '⚠️' },
    { path: '/logs', label: t('nav.logs'), icon: '📋' },
    { path: '/automation', label: t('nav.automation'), icon: '⚙️' },
    { path: '/settings', label: t('nav.settings'), icon: '⚙️' },
  ]

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h1>PROKVANT</h1>
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? '◀' : '▶'}
          </button>
        </div>
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {sidebarOpen && <span className="nav-label">{item.label}</span>}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button onClick={toggleLanguage} className="lang-toggle">
            {i18n.language === 'ru' ? '🇷🇺 RU' : '🇬🇧 EN'}
          </button>
        </div>
      </aside>
      <main className="main-content">
        <header className="top-header">
          <h2>{menuItems.find(item => item.path === location.pathname)?.label || 'PROKVANT'}</h2>
        </header>
        <div className="content">{children}</div>
      </main>
    </div>
  )
}

export default Layout
