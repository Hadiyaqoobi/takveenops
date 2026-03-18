import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Plus, FolderKanban, ClipboardList, BarChart3,
  Mic, Settings, User, ScanSearch,
} from 'lucide-react';
import { getTasks } from '../api';
import './CommandPalette.css';

const NAV_ACTIONS = [
  { id: 'nav-board', label: 'Go to Board', icon: FolderKanban, path: '/' },
  { id: 'nav-list', label: 'Go to Work Items', icon: ClipboardList, path: '/list' },
  { id: 'nav-standup', label: 'Go to Standups', icon: Mic, path: '/standup' },
  { id: 'nav-scanner', label: 'Go to Scanner', icon: ScanSearch, path: '/scanner' },
  { id: 'nav-analytics', label: 'Go to Analytics', icon: BarChart3, path: '/analytics' },
  { id: 'nav-settings', label: 'Go to Settings', icon: Settings, path: '/settings' },
  { id: 'nav-profile', label: 'Go to Profile', icon: User, path: '/profile' },
];

const QUICK_ACTIONS = [
  { id: 'create-task', label: 'Create New Task', icon: Plus, action: 'create' },
];

export default function CommandPalette({ open, onClose, onCreateTask }) {
  const [query, setQuery] = useState('');
  const [tasks, setTasks] = useState([]);
  const [results, setResults] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
      getTasks().then(setTasks).catch(() => {});
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    const q = query.toLowerCase().trim();
    const items = [];

    QUICK_ACTIONS.forEach((a) => {
      if (!q || a.label.toLowerCase().includes(q)) {
        items.push({ type: 'action', ...a });
      }
    });

    NAV_ACTIONS.forEach((a) => {
      if (!q || a.label.toLowerCase().includes(q)) {
        items.push({ type: 'nav', ...a });
      }
    });

    if (q.length > 0) {
      const matched = tasks.filter((t) =>
        t.title.toLowerCase().includes(q) || t.id.toLowerCase().includes(q)
      ).slice(0, 8);
      matched.forEach((t) => {
        items.push({ type: 'task', id: `task-${t.id}`, label: `${t.id}: ${t.title}`, task: t });
      });
    }

    setResults(items);
    setSelectedIndex(0);
  }, [query, tasks]);

  const executeItem = useCallback((item) => {
    onClose();
    if (item.type === 'nav') {
      navigate(item.path);
    } else if (item.type === 'action' && item.action === 'create') {
      onCreateTask?.();
    } else if (item.type === 'task') {
      navigate('/');
    }
  }, [navigate, onClose, onCreateTask]);

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (results[selectedIndex]) executeItem(results[selectedIndex]);
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div className="cmd-overlay" onClick={onClose}>
      <div className="cmd-palette" onClick={(e) => e.stopPropagation()}>
        <div className="cmd-input-row">
          <Search size={16} className="cmd-search-icon" />
          <input
            ref={inputRef}
            className="cmd-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search tasks, navigate, or run actions..."
          />
          <kbd className="cmd-kbd">Esc</kbd>
        </div>
        <div className="cmd-results">
          {results.map((item, i) => {
            const Icon = item.icon || Search;
            return (
              <div
                key={item.id}
                className={`cmd-result ${i === selectedIndex ? 'cmd-result-active' : ''}`}
                onClick={() => executeItem(item)}
                onMouseEnter={() => setSelectedIndex(i)}
              >
                <Icon size={14} className="cmd-result-icon" />
                <span className="cmd-result-label">{item.label}</span>
                <span className="cmd-result-type">{item.type}</span>
              </div>
            );
          })}
          {results.length === 0 && query && (
            <div className="cmd-empty">No results for "{query}"</div>
          )}
        </div>
      </div>
    </div>
  );
}
