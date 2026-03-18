import { useState, useEffect } from 'react';
import { Sun, Clock, Bell, Zap, ExternalLink } from 'lucide-react';
import { getMyDay } from '../api';
import { useAuth } from '../contexts/AuthContext';
import './MyDayPage.css';

const STATUS_LABELS = { backlog: 'New', 'in-progress': 'Active', review: 'Resolved', done: 'Closed', blocked: 'Blocked' };

export default function MyDayPage() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyDay()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="myday-loading">Loading your day...</div>;

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <>
      <div className="page-header">
        <h1><Sun size={16} /> My Day</h1>
      </div>

      <div className="page-body">
        <div className="myday-greeting">
          {greeting()}, <strong>{user?.display_name || user?.username}</strong>
        </div>

        <div className="myday-grid">
          {/* My Tasks */}
          <div className="myday-card">
            <h3><Zap size={14} /> My Tasks</h3>
            {data?.my_tasks?.length > 0 ? (
              <div className="myday-task-list">
                {data.my_tasks.map((t) => (
                  <div key={t.id} className="myday-task-item">
                    <span className={`badge badge-${t.priority?.toLowerCase()}`}>{t.priority}</span>
                    <span className="myday-task-id">{t.id}</span>
                    <span className="myday-task-title">{t.title}</span>
                    <span className={`myday-status myday-status-${t.status}`}>
                      {STATUS_LABELS[t.status] || t.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="myday-empty">No active tasks. Enjoy your day!</div>
            )}
          </div>

          {/* Deadlines */}
          <div className="myday-card">
            <h3><Clock size={14} /> Approaching Deadlines</h3>
            {data?.deadlines?.length > 0 ? (
              <div className="myday-task-list">
                {data.deadlines.map((t) => (
                  <div key={t.id} className="myday-task-item">
                    <span className="myday-due">{t.due_date}</span>
                    <span className="myday-task-id">{t.id}</span>
                    <span className="myday-task-title">{t.title}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="myday-empty">No upcoming deadlines</div>
            )}
          </div>

          {/* Recent Notifications */}
          <div className="myday-card">
            <h3><Bell size={14} /> Recent Notifications</h3>
            {data?.recent_notifications?.length > 0 ? (
              <div className="myday-notif-list">
                {data.recent_notifications.map((n) => (
                  <div key={n.id} className="myday-notif-item">
                    <span className="myday-notif-msg">{n.message}</span>
                    <span className="myday-notif-time">{new Date(n.created_at).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="myday-empty">No recent notifications</div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="myday-card">
            <h3><ExternalLink size={14} /> Quick Actions</h3>
            <div className="myday-actions">
              <a href="/board" className="myday-action-btn">Open Board</a>
              <a href="/list" className="myday-action-btn">Work Items</a>
              <a href="/standup" className="myday-action-btn">Standup</a>
              <a href="/analytics" className="myday-action-btn">Analytics</a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
