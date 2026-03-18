import { useState } from 'react';
import { Zap, Plus, X } from 'lucide-react';
import { parseTaskText, createTask } from '../api';
import './QuickAddBar.css';

export default function QuickAddBar({ onCreated }) {
  const [text, setText] = useState('');
  const [parsed, setParsed] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleParse = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const data = await parseTaskText(text);
      setParsed(data);
    } catch (e) {
      console.error('Parse failed:', e);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleParse();
    if (e.key === 'Escape') handleClear();
  };

  const handleCreate = async () => {
    if (!parsed) return;
    setLoading(true);
    try {
      await createTask({
        title: parsed.parsed.title,
        type: parsed.parsed.type,
        priority: parsed.parsed.priority,
        assignee: parsed.parsed.assignee || null,
        labels: parsed.parsed.labels || [],
        status: 'backlog',
      });
      setText('');
      setParsed(null);
      onCreated?.();
    } catch (e) {
      console.error('Create failed:', e);
    }
    setLoading(false);
  };

  const handleClear = () => {
    setText('');
    setParsed(null);
  };

  const typeColors = {
    feature: '#773b93',
    bug: '#cc293d',
    'tech-debt': '#ca5010',
    research: '#0078d4',
    ops: '#8a8886',
  };

  return (
    <div className="quick-add-bar">
      <div className="quick-add-input-row">
        <Zap size={14} className="quick-add-icon" />
        <input
          className="quick-add-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder='Try: "Fix login bug assign to admin P1" then press Enter'
        />
        {text && (
          <button className="quick-add-clear" onClick={handleClear}><X size={14} /></button>
        )}
        <button className="btn btn-ghost quick-add-parse-btn" onClick={handleParse} disabled={loading || !text.trim()}>
          {loading ? '...' : 'Parse'}
        </button>
      </div>

      {parsed && (
        <div className="quick-add-preview">
          <div className="quick-add-preview-fields">
            <span className="quick-add-field">
              <span className="quick-add-label">Title:</span> {parsed.parsed.title}
            </span>
            <span className="quick-add-field">
              <span className="quick-add-label">Type:</span>
              <span className="quick-add-type-dot" style={{ background: typeColors[parsed.parsed.type] || '#888' }} />
              {parsed.parsed.type}
            </span>
            <span className="quick-add-field">
              <span className="quick-add-label">Priority:</span> {parsed.parsed.priority}
            </span>
            {parsed.parsed.assignee && (
              <span className="quick-add-field">
                <span className="quick-add-label">Assignee:</span> {parsed.parsed.assignee}
              </span>
            )}
          </div>
          <button className="btn btn-primary quick-add-create-btn" onClick={handleCreate} disabled={loading}>
            <Plus size={13} /> Create
          </button>
        </div>
      )}
    </div>
  );
}
