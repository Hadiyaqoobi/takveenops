import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  Zap, Search, LayoutDashboard, User, LogOut,
  FolderKanban, ClipboardList, Mic, ScanSearch, BarChart3, Settings,
} from 'lucide-react';
import { useAuth } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import BoardPage from './pages/BoardPage';
import ListPage from './pages/ListPage';
import StandupPage from './pages/StandupPage';
import ScannerPage from './pages/ScannerPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';
import ProfilePage from './pages/ProfilePage';

function SidebarSection({ children }) {
  return <div className="sidebar-section">{children}</div>;
}

function SidebarLink({ to, icon: Icon, label, end }) {
  return (
    <NavLink to={to} end={end} className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
      <Icon size={16} />
      <span>{label}</span>
    </NavLink>
  );
}

function AppShell() {
  const location = useLocation();
  const { user, logout } = useAuth();

  const pageNames = {
    '/': 'Boards',
    '/list': 'Work Items',
    '/standup': 'Standups',
    '/scanner': 'Scanner',
    '/analytics': 'Analytics',
    '/settings': 'Settings',
    '/profile': 'Profile',
  };
  const currentPage = pageNames[location.pathname] || 'Boards';

  return (
    <div className="app-shell">
      {/* Blue top header */}
      <header className="global-header">
        <div className="global-logo">
          <Zap size={18} />
          TakvenOps
        </div>
        <nav className="global-breadcrumb">
          <span>/</span>
          <a href="/">Project</a>
          <span>/</span>
          <a href={location.pathname}>{currentPage}</a>
        </nav>
        <div className="global-actions">
          <button title="Search"><Search size={16} /></button>
          <NavLink to="/profile" className="header-user-link" title="My Profile">
            <div className="header-avatar">
              {user?.display_name?.slice(0, 2).toUpperCase() || '??'}
            </div>
            <span className="header-username">{user?.display_name || user?.username}</span>
          </NavLink>
          <button title="Sign Out" onClick={logout} className="header-logout-btn">
            <LogOut size={15} />
          </button>
        </div>
      </header>

      {/* Sidebar + main */}
      <div className="app-body">
        <aside className="sidebar">
          <div className="sidebar-project">
            <div className="sidebar-project-icon">TO</div>
            <div className="sidebar-project-name">TakvenOps</div>
          </div>

          <SidebarSection>
            <SidebarLink to="/" icon={LayoutDashboard} label="Overview" end />
          </SidebarSection>

          <SidebarSection>
            <SidebarLink to="/" icon={FolderKanban} label="Boards" end />
            <SidebarLink to="/list" icon={ClipboardList} label="Work Items" />
            <SidebarLink to="/standup" icon={Mic} label="Standups" />
            <SidebarLink to="/scanner" icon={ScanSearch} label="Scanner" />
          </SidebarSection>

          <SidebarSection>
            <SidebarLink to="/analytics" icon={BarChart3} label="Analytics" />
          </SidebarSection>

          <div className="sidebar-footer">
            <SidebarLink to="/profile" icon={User} label="My Profile" />
            <SidebarLink to="/settings" icon={Settings} label="Project Settings" />
          </div>
        </aside>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<BoardPage />} />
            <Route path="/list" element={<ListPage />} />
            <Route path="/standup" element={<StandupPage />} />
            <Route path="/scanner" element={<ScannerPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function AuthGate() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg-page)' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: 14 }}>Loading...</span>
      </div>
    );
  }

  if (!user) return <LoginPage />;
  return <AppShell />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthGate />
    </BrowserRouter>
  );
}
