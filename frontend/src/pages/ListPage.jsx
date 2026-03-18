import { useState, useEffect } from 'react';
import { Plus, ArrowUpDown, CheckSquare } from 'lucide-react';
import TaskDetail from '../components/TaskDetail';
import CreateTaskModal from '../components/CreateTaskModal';
import BulkActionBar from '../components/BulkActionBar';
import { getTasks } from '../api';
import { useProject } from '../contexts/ProjectContext';
import './ListPage.css';

const priorityOrder = { P0: 0, P1: 1, P2: 2, P3: 3 };
const STATUS_LABELS = { backlog: 'New', 'in-progress': 'Active', review: 'Resolved', done: 'Closed', blocked: 'Blocked' };
const TYPE_COLORS = { feature: '#773b93', bug: '#cc293d', 'tech-debt': '#ca5010', research: '#0078d4', ops: '#8a8886' };

export default function ListPage() {
  const { currentProject } = useProject();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [sortField, setSortField] = useState('priority');
  const [sortDir, setSortDir] = useState('asc');
  const [bulkMode, setBulkMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const loadTasks = async () => {
    try { setTasks(await getTasks({ project_id: currentProject })); } catch (e) { console.error(e); }
  };
  useEffect(() => { loadTasks(); }, [currentProject]);

  const toggleSort = (field) => {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortField(field); setSortDir('asc'); }
  };

  const sorted = [...tasks].sort((a, b) => {
    let cmp = 0;
    if (sortField === 'priority') cmp = (priorityOrder[a.priority] ?? 9) - (priorityOrder[b.priority] ?? 9);
    else if (sortField === 'title') cmp = (a.title || '').localeCompare(b.title || '');
    else if (sortField === 'status') cmp = (a.status || '').localeCompare(b.status || '');
    else if (sortField === 'assignee') cmp = (a.assignee || 'zzz').localeCompare(b.assignee || 'zzz');
    else if (sortField === 'type') cmp = (a.type || '').localeCompare(b.type || '');
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const SortHeader = ({ field, children }) => (
    <th onClick={() => toggleSort(field)} className="sortable-th">
      {children}
      {sortField === field && <ArrowUpDown size={10} />}
    </th>
  );

  return (
    <>
      <div className="page-header">
        <h1>Work Items</h1>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={13} /> New Work Item
          </button>
          <button
            className={`btn btn-ghost ${bulkMode ? 'btn-active' : ''}`}
            onClick={() => { setBulkMode(!bulkMode); setSelectedIds(new Set()); }}
          >
            <CheckSquare size={14} /> Bulk
          </button>
        </div>
      </div>

      <div className="list-container">
        <div className="list-table-wrap">
          <table className="list-table">
            <thead>
              <tr>
                {bulkMode && <th style={{ width: 28 }}></th>}
                <th style={{ width: 28 }}></th>
                <th style={{ width: 80 }}>ID</th>
                <SortHeader field="priority">Priority</SortHeader>
                <SortHeader field="title">Title</SortHeader>
                <SortHeader field="type">Type</SortHeader>
                <SortHeader field="status">State</SortHeader>
                <SortHeader field="assignee">Assigned To</SortHeader>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((t) => {
                const typeColor = TYPE_COLORS[t.type] || '#0078d4';
                const labels = Array.isArray(t.labels) ? t.labels : [];
                return (
                  <tr key={t.id} onClick={() => !bulkMode && setSelectedTask(t)} className="list-row">
                    {bulkMode && (
                      <td onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(t.id)}
                          onChange={() => toggleSelect(t.id)}
                        />
                      </td>
                    )}
                    <td>
                      <div className="list-type-icon" style={{ background: typeColor }}>
                        <svg width="10" height="10" viewBox="0 0 16 16" fill="white">
                          <rect x="2" y="2" width="12" height="12" rx="2" />
                        </svg>
                      </div>
                    </td>
                    <td className="col-id">{t.id}</td>
                    <td><span className={`badge badge-${t.priority?.toLowerCase()}`}>{t.priority}</span></td>
                    <td className="col-title">{t.title}</td>
                    <td className="col-type">{t.type}</td>
                    <td>
                      <span className={`status-dot status-dot-${t.status}`} />
                      {STATUS_LABELS[t.status] || t.status}
                    </td>
                    <td className="col-assignee">{t.assignee || '—'}</td>
                    <td>
                      <div className="list-tags">
                        {labels.slice(0, 3).map((l) => <span key={l} className="label-chip">{l}</span>)}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {sorted.length === 0 && (
                <tr><td colSpan={bulkMode ? 9 : 8} className="empty-row">No work items found.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {selectedTask && (
          <TaskDetail
            task={selectedTask}
            onClose={() => setSelectedTask(null)}
            onUpdate={() => { loadTasks(); setSelectedTask(null); }}
          />
        )}
      </div>

      {showCreate && <CreateTaskModal onClose={() => setShowCreate(false)} onCreated={loadTasks} />}

      {bulkMode && (
        <BulkActionBar
          selectedIds={[...selectedIds]}
          onClear={() => setSelectedIds(new Set())}
          onDone={() => { setSelectedIds(new Set()); setBulkMode(false); loadTasks(); }}
        />
      )}
    </>
  );
}
