import { useState, useEffect } from 'react';
import { Target, Plus, Minus, AlertTriangle, Users, ChevronDown, Wand2, Download } from 'lucide-react';
import { getSprints, getSprintSuggestions, addTaskToSprint, removeTaskFromSprint, autoAssignTasks, getSprintReport, downloadSprintReportCSV } from '../api';
import './SprintPlanningPage.css';

const TYPE_COLORS = {
  feature: '#773b93', bug: '#cc293d', 'tech-debt': '#ca5010',
  research: '#0078d4', ops: '#8a8886',
};

export default function SprintPlanningPage() {
  const [sprints, setSprints] = useState([]);
  const [selectedSprint, setSelectedSprint] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoAssigning, setAutoAssigning] = useState(false);

  useEffect(() => {
    getSprints().then((s) => {
      setSprints(s);
      if (s.length > 0) setSelectedSprint(s[0].id);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedSprint) return;
    setLoading(true);
    getSprintSuggestions(selectedSprint)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedSprint]);

  const handleAdd = async (taskId) => {
    await addTaskToSprint(selectedSprint, taskId);
    const d = await getSprintSuggestions(selectedSprint);
    setData(d);
  };

  const handleRemove = async (taskId) => {
    await removeTaskFromSprint(selectedSprint, taskId);
    const d = await getSprintSuggestions(selectedSprint);
    setData(d);
  };

  const handleAutoAssignSprint = async () => {
    if (!data?.sprint_tasks) return;
    setAutoAssigning(true);
    try {
      const unassigned = data.sprint_tasks.filter((t) => !t.assignee).map((t) => t.id);
      if (unassigned.length === 0) { alert('All sprint tasks are already assigned.'); setAutoAssigning(false); return; }
      await autoAssignTasks(unassigned);
      const d = await getSprintSuggestions(selectedSprint);
      setData(d);
    } catch (e) {
      console.error('Auto-assign failed:', e);
    }
    setAutoAssigning(false);
  };

  return (
    <>
      <div className="page-header">
        <h1><Target size={16} /> Sprint Planning</h1>
        <div className="page-header-actions">
          <select
            className="filter-select"
            value={selectedSprint || ''}
            onChange={(e) => setSelectedSprint(Number(e.target.value))}
          >
            {sprints.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          {selectedSprint && (
            <>
              <button
                className="btn btn-ghost"
                onClick={handleAutoAssignSprint}
                disabled={autoAssigning}
                title="Auto-assign unassigned sprint tasks"
              >
                <Wand2 size={14} /> {autoAssigning ? 'Assigning...' : 'Auto-Assign'}
              </button>
              <button
                className="btn btn-ghost"
                onClick={() => downloadSprintReportCSV(selectedSprint)}
                title="Export sprint report as CSV"
              >
                <Download size={14} /> Export CSV
              </button>
            </>
          )}
        </div>
      </div>

      <div className="page-body">
        {sprints.length === 0 && (
          <div className="sprint-empty">No sprints yet. Create one in Settings first.</div>
        )}

        {loading && <div className="sprint-loading">Loading sprint data...</div>}

        {data && !loading && (
          <>
            {/* Warnings */}
            {data.warnings?.length > 0 && (
              <div className="sprint-warnings">
                {data.warnings.map((w, i) => (
                  <div key={i} className="sprint-warning-item">
                    <AlertTriangle size={13} /> {w}
                  </div>
                ))}
              </div>
            )}

            {/* Team capacity cards */}
            <div className="capacity-cards">
              <h3><Users size={14} /> Team Capacity</h3>
              <div className="capacity-grid">
                {data.team_capacity?.map((m) => (
                  <div key={m.name} className="capacity-card">
                    <div className="capacity-name">{m.name}</div>
                    <div className="capacity-bar-wrap">
                      <div
                        className={`capacity-bar ${m.current >= m.capacity ? 'capacity-full' : ''}`}
                        style={{ width: `${Math.min(100, (m.current / m.capacity) * 100)}%` }}
                      />
                    </div>
                    <div className="capacity-label">{m.current}/{m.capacity} tasks</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Two-column layout */}
            <div className="sprint-columns">
              {/* Backlog / Suggestions */}
              <div className="sprint-col">
                <h3>Suggested Tasks ({data.suggestions?.length || 0})</h3>
                <div className="sprint-task-list">
                  {data.suggestions?.map((t) => (
                    <div key={t.id} className="sprint-task-item">
                      <div className="sprint-task-type" style={{ background: TYPE_COLORS[t.type] || '#888' }} />
                      <div className="sprint-task-info">
                        <span className="sprint-task-id">{t.id}</span>
                        <span className="sprint-task-title">{t.title}</span>
                        <span className={`badge badge-${t.priority?.toLowerCase()}`}>{t.priority}</span>
                      </div>
                      <button className="btn btn-ghost" onClick={() => handleAdd(t.id)} title="Add to sprint">
                        <Plus size={14} />
                      </button>
                    </div>
                  ))}
                  {data.suggestions?.length === 0 && (
                    <div className="sprint-empty">No tasks to suggest</div>
                  )}
                </div>
              </div>

              {/* Sprint Tasks */}
              <div className="sprint-col">
                <h3>Sprint Tasks ({data.sprint_tasks?.length || 0})</h3>
                <div className="sprint-task-list">
                  {data.sprint_tasks?.map((t) => (
                    <div key={t.id} className="sprint-task-item">
                      <div className="sprint-task-type" style={{ background: TYPE_COLORS[t.type] || '#888' }} />
                      <div className="sprint-task-info">
                        <span className="sprint-task-id">{t.id}</span>
                        <span className="sprint-task-title">{t.title}</span>
                        <span className={`badge badge-${t.status === 'done' ? 'done' : t.priority?.toLowerCase()}`}>
                          {t.status === 'done' ? 'Done' : t.priority}
                        </span>
                      </div>
                      <button className="btn btn-ghost" onClick={() => handleRemove(t.id)} title="Remove from sprint">
                        <Minus size={14} />
                      </button>
                    </div>
                  ))}
                  {data.sprint_tasks?.length === 0 && (
                    <div className="sprint-empty">No tasks in this sprint yet</div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}
