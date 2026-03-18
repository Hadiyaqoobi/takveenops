import { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  Zap, Search, LayoutDashboard, User, LogOut, Moon, Sun,
  FolderKanban, ClipboardList, Mic, ScanSearch, BarChart3, Settings, Target,
  Sun as SunIcon, CalendarDays,
} from 'lucide-react';
import { useAuth } from './contexts/AuthContext';
import { useTheme } from './contexts/ThemeContext';
import { useProject } from './contexts/ProjectContext';
import { UPLOADS_BASE } from './api';
import useKeyboardShortcuts from './hooks/useKeyboardShortcuts';
import CommandPalette from './components/CommandPalette';
import ShortcutsModal from './components/ShortcutsModal';
import CreateTaskModal from './components/CreateTaskModal';
import NotificationBell from './components/NotificationBell';
import InstallPrompt from './components/InstallPrompt';
import LoginPage from './pages/LoginPage';
import BoardPage from './pages/BoardPage';
import ListPage from './pages/ListPage';
import StandupPage from './pages/StandupPage';
import ScannerPage from './pages/ScannerPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';
import ProfilePage from './pages/ProfilePage';
import SprintPlanningPage from './pages/SprintPlanningPage';
import MyDayPage from './pages/MyDayPage';
import CalendarPage from './pages/CalendarPage';

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
  const { theme, toggleTheme } = useTheme();
  const { projects, currentProject, currentProjectData, selectProject } = useProject();
  const [showCmdPalette, setShowCmdPalette] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showCreateTask, setShowCreateTask] = useState(false);

  const closeAll = useCallback(() => {
    setShowCmdPalette(false);
    setShowShortcuts(false);
    setShowCreateTask(false);
  }, []);

  useKeyboardShortcuts({
    onCreateTask: () => setShowCreateTask(true),
    onOpenPalette: () => setShowCmdPalette((v) => !v),
    onShowHelp: () => setShowShortcuts(true),
    onEscape: closeAll,
  });

  const pageNames = {
    '/': 'My Day',
    '/board': 'Boards',
    '/list': 'Work Items',
    '/standup': 'Standups',
    '/scanner': 'Scanner',
    '/analytics': 'Analytics',
    '/sprint-planning': 'Sprint Planning',
    '/calendar': 'Calendar',
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
          <button title={theme === 'light' ? 'Dark Mode' : 'Light Mode'} onClick={toggleTheme}>
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
          </button>
          <NotificationBell />
          <button title="Search (Ctrl+K)" onClick={() => setShowCmdPalette(true)}>
            <Search size={16} />
          </button>
          <NavLink to="/profile" className="header-user-link" title="My Profile">
            <div className="header-avatar">
              {user?.avatar_url ? (
                <img src={`${UPLOADS_BASE}${user.avatar_url}`} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
              ) : (
                user?.display_name?.slice(0, 2).toUpperCase() || '??'
              )}
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
            <div className="sidebar-project-icon">
              {currentProjectData?.key?.slice(0, 2) || 'TO'}
            </div>
            {projects.length > 1 ? (
              <select
                value={currentProject}
                onChange={(e) => selectProject(e.target.value)}
                className="sidebar-project-select"
              >
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            ) : (
              <div className="sidebar-project-name">{currentProjectData?.name || 'TakvenOps'}</div>
            )}
          </div>

          <SidebarSection>
            <SidebarLink to="/" icon={SunIcon} label="My Day" end />
          </SidebarSection>

          <SidebarSection>
            <SidebarLink to="/board" icon={FolderKanban} label="Boards" />
            <SidebarLink to="/list" icon={ClipboardList} label="Work Items" />
            <SidebarLink to="/calendar" icon={CalendarDays} label="Calendar" />
            <SidebarLink to="/standup" icon={Mic} label="Standups" />
            <SidebarLink to="/scanner" icon={ScanSearch} label="Scanner" />
          </SidebarSection>

          <SidebarSection>
            <SidebarLink to="/analytics" icon={BarChart3} label="Analytics" />
            <SidebarLink to="/sprint-planning" icon={Target} label="Sprint Planning" />
          </SidebarSection>

          <div className="sidebar-footer">
            <SidebarLink to="/profile" icon={User} label="My Profile" />
            <SidebarLink to="/settings" icon={Settings} label="Project Settings" />
          </div>
        </aside>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<MyDayPage />} />
            <Route path="/board" element={<BoardPage />} />
            <Route path="/list" element={<ListPage />} />
            <Route path="/calendar" element={<CalendarPage />} />
            <Route path="/standup" element={<StandupPage />} />
            <Route path="/scanner" element={<ScannerPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/sprint-planning" element={<SprintPlanningPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Routes>
        </main>
      </div>

      {/* Global overlays */}
      <CommandPalette
        open={showCmdPalette}
        onClose={() => setShowCmdPalette(false)}
        onCreateTask={() => { setShowCmdPalette(false); setShowCreateTask(true); }}
      />
      {showShortcuts && <ShortcutsModal onClose={() => setShowShortcuts(false)} />}
      {showCreateTask && (
        <CreateTaskModal onClose={() => setShowCreateTask(false)} onCreated={() => setShowCreateTask(false)} />
      )}
      <InstallPrompt />
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
