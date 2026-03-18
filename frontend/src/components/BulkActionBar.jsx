import { useState } from 'react';
import { X, UserPlus, ArrowRight, Trash2 } from 'lucide-react';
import { bulkAction } from '../api';
import AssigneeSelect from './AssigneeSelect';
import './BulkActionBar.css';

export default function BulkActionBar({ selectedIds, onClear, onDone }) {
  const [action, setAction] = useState(null);
  const [assignee, setAssignee] = useState('');
  const [status, setStatus] = useState('backlog');
  const [loading, setLoading] = useState(false);

  if (selectedIds.length === 0) return null;

  const handleExecute = async () => {
    setLoading(true);
    try {
      if (action === 'assign') {
        await bulkAction('assign', selectedIds, { assignee });
      } else if (action === 'move') {
        await bulkAction('move', selectedIds, { status });
      } else if (action === 'delete') {
        if (!window.confirm(`Delete ${selectedIds.length} task(s)?`)) {
          setLoading(false);
          return;
        }
        await bulkAction('delete', selectedIds);
      }
      setAction(null);
      onDone?.();
    } catch (e) {
      console.error('Bulk action failed:', e);
    }
    setLoading(false);
  };

  return (
    <div className="bulk-bar">
      <div className="bulk-bar-info">
        <span className="bulk-count">{selectedIds.length} selected</span>
        <button className="btn btn-ghost bulk-clear" onClick={onClear}><X size={13} /></button>
      </div>

      <div className="bulk-bar-actions">
        {!action && (
          <>
            <button className="btn btn-ghost" onClick={() => setAction('assign')}><UserPlus size={13} /> Assign</button>
            <button className="btn btn-ghost" onClick={() => setAction('move')}><ArrowRight size={13} /> Move</button>
            <button className="btn btn-ghost bulk-delete-btn" onClick={() => { setAction('delete'); }}><Trash2 size={13} /> Delete</button>
          </>
        )}

        {action === 'assign' && (
          <div className="bulk-inline">
            <AssigneeSelect value={assignee} onChange={setAssignee} />
            <button className="btn btn-primary" onClick={handleExecute} disabled={loading || !assignee}>Apply</button>
            <button className="btn btn-ghost" onClick={() => setAction(null)}>Cancel</button>
          </div>
        )}

        {action === 'move' && (
          <div className="bulk-inline">
            <select className="filter-select" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="backlog">New</option>
              <option value="in-progress">Active</option>
              <option value="review">Resolved</option>
              <option value="done">Closed</option>
              <option value="blocked">Blocked</option>
            </select>
            <button className="btn btn-primary" onClick={handleExecute} disabled={loading}>Apply</button>
            <button className="btn btn-ghost" onClick={() => setAction(null)}>Cancel</button>
          </div>
        )}

        {action === 'delete' && (
          <div className="bulk-inline">
            <button className="btn btn-primary" onClick={handleExecute} disabled={loading} style={{ background: '#cc293d' }}>
              Confirm Delete
            </button>
            <button className="btn btn-ghost" onClick={() => setAction(null)}>Cancel</button>
          </div>
        )}
      </div>
    </div>
  );
}
