import { useState, useEffect } from 'react';
import { User, Save, CheckCircle, Clock, AlertCircle, Layers } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { getProfileDashboard, updateProfile } from '../api';
import './ProfilePage.css';

const STATUS_LABELS = {
  backlog: 'New',
  'in-progress': 'Active',
  review: 'Resolved',
  done: 'Closed',
  blocked: 'Blocked',
};

const PRIORITY_CLASSES = { P0: 'p0', P1: 'p1', P2: 'p2', P3: 'p3' };

export default function ProfilePage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({ display_name: '', email: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getProfileDashboard()
      .then(setDashboard)
      .catch((e) => console.error('Failed to load dashboard:', e));
  }, []);

  const startEdit = () => {
    setEditForm({ display_name: user.display_name || '', email: user.email || '' });
    setEditing(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateProfile(editForm);
      setEditing(false);
      // Refresh dashboard
      setDashboard(await getProfileDashboard());
    } catch (e) {
      console.error('Update failed:', e);
    }
    setSaving(false);
  };

  const stats = dashboard?.stats || {};
  const tasks = dashboard?.assigned_tasks || [];
  const activity = dashboard?.recent_activity || [];

  return (
    <>
      <div className="page-header">
        <h1>My Profile</h1>
      </div>

      {/* Profile header */}
      <div className="profile-header-card">
        <div className="profile-avatar-large">
          {user?.display_name?.slice(0, 2).toUpperCase() || '??'}
        </div>
        <div className="profile-info">
          {editing ? (
            <div className="profile-edit-form">
              <input
                value={editForm.display_name}
                onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                placeholder="Display Name"
              />
              <input
                value={editForm.email}
                onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                placeholder="Email"
              />
              <div className="profile-edit-actions">
                <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                  <Save size={13} /> {saving ? 'Saving...' : 'Save'}
                </button>
                <button className="btn btn-secondary" onClick={() => setEditing(false)}>Cancel</button>
              </div>
            </div>
          ) : (
            <>
              <h2>{user?.display_name || user?.username}</h2>
              <span className="profile-email">{user?.email || 'No email set'}</span>
              <span className="profile-role">{user?.role || 'member'}</span>
              <button className="btn btn-ghost profile-edit-btn" onClick={startEdit}>Edit Profile</button>
            </>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="profile-stats">
        <div className="profile-stat-card">
          <Layers size={18} />
          <div className="profile-stat-value">{stats.total || 0}</div>
          <div className="profile-stat-label">Total Tasks</div>
        </div>
        <div className="profile-stat-card">
          <Clock size={18} />
          <div className="profile-stat-value">{stats['in-progress'] || 0}</div>
          <div className="profile-stat-label">In Progress</div>
        </div>
        <div className="profile-stat-card">
          <CheckCircle size={18} />
          <div className="profile-stat-value">{stats.done || 0}</div>
          <div className="profile-stat-label">Completed</div>
        </div>
        <div className="profile-stat-card">
          <AlertCircle size={18} />
          <div className="profile-stat-value">{stats.blocked || 0}</div>
          <div className="profile-stat-label">Blocked</div>
        </div>
      </div>

      {/* My Tasks */}
      <div className="profile-section">
        <h3>My Assigned Tasks</h3>
        {tasks.length === 0 ? (
          <div className="profile-empty">No tasks assigned to you</div>
        ) : (
          <table className="list-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Type</th>
                <th>Priority</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td className="list-id">{t.id}</td>
                  <td>{t.title}</td>
                  <td><span className="label-chip">{t.type}</span></td>
                  <td><span className={`priority-badge ${PRIORITY_CLASSES[t.priority] || ''}`}>{t.priority}</span></td>
                  <td>{STATUS_LABELS[t.status] || t.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Recent Activity */}
      <div className="profile-section">
        <h3>Recent Activity</h3>
        {activity.length === 0 ? (
          <div className="profile-empty">No recent activity</div>
        ) : (
          <div className="profile-activity-list">
            {activity.map((a) => (
              <div key={a.id} className="profile-activity-item">
                <div className="profile-activity-dot" />
                <div className="profile-activity-content">
                  <span className="profile-activity-action">
                    <strong>{a.actor || 'System'}</strong> {a.action} <code>{a.task_id}</code>
                    {a.from_status && a.to_status && (
                      <> from {STATUS_LABELS[a.from_status] || a.from_status} to {STATUS_LABELS[a.to_status] || a.to_status}</>
                    )}
                  </span>
                  <span className="profile-activity-time">{new Date(a.timestamp).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
