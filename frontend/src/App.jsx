import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import Upload from './pages/Upload.jsx'
import Chat from './pages/Chat.jsx'
import Maintenance from './pages/Maintenance.jsx'
import Compliance from './pages/Compliance.jsx'
import Lessons from './pages/Lessons.jsx'
import Search from './pages/Search.jsx'
import FieldTech from './pages/FieldTech.jsx'

/**
 * App shell — dark sidebar navigation + routed content area.
 */
export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        {/* ── Sidebar ── */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="sidebar-logo">
              <div className="sidebar-logo-icon">⚙</div>
              <div className="sidebar-logo-text">
                <h1>Operations Brain</h1>
                <span>Industrial AI Platform</span>
              </div>
            </div>
          </div>

          <nav className="sidebar-nav">
            <div className="sidebar-section-label">Overview</div>
            <NavLink
              to="/"
              end
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">📊</span>
              <span>Dashboard</span>
            </NavLink>
            <NavLink
              to="/search"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">🔍</span>
              <span>Hybrid Search</span>
            </NavLink>

            <div className="sidebar-section-label">Data Ingestion</div>
            <NavLink
              to="/upload"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">📄</span>
              <span>Document Upload</span>
            </NavLink>

            <div className="sidebar-section-label">Intelligence & Safety</div>
            <NavLink
              to="/chat"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">🤖</span>
              <span>Knowledge Copilot</span>
            </NavLink>
            <NavLink
              to="/maintenance"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">🔧</span>
              <span>Maintenance Intel</span>
            </NavLink>
            <NavLink
              to="/compliance"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">🦺</span>
              <span>Compliance Dashboard</span>
            </NavLink>
            <NavLink
              to="/lessons"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">💡</span>
              <span>Lessons Learned</span>
            </NavLink>

            <div className="sidebar-section-label">Field Execution</div>
            <NavLink
              to="/field-tech"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">📱</span>
              <span>Field Tech Mode</span>
            </NavLink>
          </nav>

          <div className="sidebar-footer">
            <p>Hackathon Prototype v1.0</p>
          </div>
        </aside>

        {/* ── Main Content ── */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/maintenance" element={<Maintenance />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/lessons" element={<Lessons />} />
            <Route path="/search" element={<Search />} />
            <Route path="/field-tech" element={<FieldTech />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
