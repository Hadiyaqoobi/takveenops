import { useState, useEffect } from 'react';
import { Mic, RefreshCw, CheckCircle, Clock, Eye, AlertOctagon, AlertTriangle } from 'lucide-react';
import { getStandup } from '../api';
import './StandupPage.css';

export default function StandupPage() {
  const [standup, setStandup] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setStandup(await getStandup());
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  return (
    <>
      <div className="page-header">
        <h1><Mic size={16} /> Daily Standup</h1>
        <button className="btn btn-secondary" onClick={load}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="page-body">
        {loading && <div className="standup-loading">Loading standup...</div>}

        {standup && !loading && (
          <div className="standup-report fade-in">
            <div className="standup-date">{standup.date}</div>

            <StandupSection
              icon={<CheckCircle size={14} />}
              title="Completed"
              color="var(--status-done)"
              tasks={standup.completed}
              empty="No tasks completed yet"
            />

            <StandupSection
              icon={<Clock size={14} />}
              title="In Progress"
              color="var(--status-progress)"
              tasks={standup.in_progress}
              empty="Nothing in progress"
            />

            <StandupSection
              icon={<Eye size={14} />}
              title="Awaiting Review"
              color="var(--status-review)"
              tasks={standup.review}
              empty="No tasks in review"
            />

            <StandupSection
              icon={<AlertOctagon size={14} />}
              title="Blocked"
              color="var(--status-blocked)"
              tasks={standup.blocked}
              empty="Nothing blocked"
            />

            {standup.high_priority_backlog?.length > 0 && (
              <StandupSection
                icon={<AlertTriangle size={14} />}
                title="High Priority Backlog"
                color="var(--p0-color)"
                tasks={standup.high_priority_backlog}
              />
            )}

            <div className="standup-progress">
              <h3>Sprint Progress</h3>
              <div className="progress-bar-wrap">
                <div className="progress-bar" style={{ width: `${standup.progress.percentage}%` }} />
              </div>
              <div className="progress-label">
                {standup.progress.done}/{standup.progress.total} tasks ({standup.progress.percentage}%)
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function StandupSection({ icon, title, color, tasks, empty }) {
  return (
    <div className="standup-section">
      <h3 style={{ color }}>
        {icon} {title} <span className="section-count">{tasks?.length || 0}</span>
      </h3>
      {tasks?.length > 0 ? (
        <ul>
          {tasks.map((t) => (
            <li key={t.id}>
              <span className="standup-task-id">{t.id}</span>
              <span>{t.title}</span>
              {t.assignee && <span className="standup-assignee">{t.assignee}</span>}
            </li>
          ))}
        </ul>
      ) : (
        <div className="standup-empty">{empty}</div>
      )}
    </div>
  );
}
