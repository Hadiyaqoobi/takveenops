import { useState, useEffect } from 'react';
import { X, Save, Trash2, MessageSquare, Activity, Send, GitPullRequest, GitCommit, Clock, Plus, Paperclip, FileText } from 'lucide-react';
import { updateTask, deleteTask, getComments, addComment, getTaskActivity, getTaskLinks, getTimeEntries, logTime, deleteTimeEntry, uploadTaskAttachment, getTaskAttachments, deleteTaskAttachment, UPLOADS_BASE } from '../api';
import AssigneeSelect from './AssigneeSelect';
import MentionInput from './MentionInput';
import './TaskDetail.css';

const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];
const formatBytes = (bytes) => {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};
const STATUSES = ['backlog', 'in-progress', 'review', 'done', 'blocked'];
const PRIORITIES = ['P0', 'P1', 'P2', 'P3'];
const TYPES = ['feature', 'bug', 'tech-debt', 'research', 'ops'];
const STATUS_LABELS = { backlog: 'New', 'in-progress': 'Active', review: 'Resolved', done: 'Closed', blocked: 'Blocked' };
const TYPE_COLORS = { feature: '#773b93', bug: '#cc293d', 'tech-debt': '#ca5010', research: '#0078d4', ops: '#8a8886' };

export default function TaskDetail({ task, onClose, onUpdate }) {
  const [form, setForm] = useState({ ...task });
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('comments');
  const [comments, setComments] = useState([]);
  const [activities, setActivities] = useState([]);
  const [links, setLinks] = useState([]);
  const [commentText, setCommentText] = useState('');
  const [sendingComment, setSendingComment] = useState(false);
  const [timeEntries, setTimeEntries] = useState([]);
  const [timeForm, setTimeForm] = useState({ hours: '', description: '' });
  const [loggingTime, setLoggingTime] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => { setForm({ ...task }); }, [task]);

  useEffect(() => {
    if (!task) return;
    getComments(task.id).then(setComments).catch(() => {});
    getTaskActivity(task.id).then(setActivities).catch(() => {});
    getTaskLinks(task.id).then(setLinks).catch(() => setLinks([]));
    getTimeEntries(task.id).then(setTimeEntries).catch(() => setTimeEntries([]));
    getTaskAttachments(task.id).then(setAttachments).catch(() => setAttachments([]));
  }, [task?.id]);

  const handleLogTime = async () => {
    if (!timeForm.hours) return;
    setLoggingTime(true);
    try {
      await logTime(task.id, { hours: parseFloat(timeForm.hours), description: timeForm.description });
      setTimeForm({ hours: '', description: '' });
      setTimeEntries(await getTimeEntries(task.id));
    } catch (e) {
      console.error('Log time failed:', e);
    }
    setLoggingTime(false);
  };

  const handleDeleteTime = async (entryId) => {
    try {
      await deleteTimeEntry(task.id, entryId);
      setTimeEntries(await getTimeEntries(task.id));
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpload = async (files) => {
    setUploading(true);
    try {
      for (const file of files) {
        await uploadTaskAttachment(task.id, file);
      }
      setAttachments(await getTaskAttachments(task.id));
    } catch (e) {
      console.error('Upload failed:', e);
    }
    setUploading(false);
  };

  const handleDeleteAttachment = async (id) => {
    try {
      await deleteTaskAttachment(task.id, id);
      setAttachments(await getTaskAttachments(task.id));
    } catch (e) {
      console.error(e);
    }
  };

  if (!task) return null;

  const handleAddComment = async () => {
    if (!commentText.trim()) return;
    setSendingComment(true);
    try {
      await addComment(task.id, commentText);
      setCommentText('');
      setComments(await getComments(task.id));
      setActivities(await getTaskActivity(task.id));
    } catch (e) {
      console.error('Comment failed:', e);
    }
    setSendingComment(false);
  };

  const handleChange = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateTask(task.id, {
        title: form.title,
        type: form.type,
        priority: form.priority,
        status: form.status,
        assignee: form.assignee || null,
        due_date: form.due_date || null,
        estimated_hours: form.estimated_hours ? parseFloat(form.estimated_hours) : null,
        body_markdown: form.body_markdown || '',
        labels: form.labels || [],
      });
      onUpdate?.();
    } catch (e) {
      console.error('Save failed:', e);
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    if (window.confirm(`Delete ${task.id}?`)) {
      await deleteTask(task.id);
      onUpdate?.();
      onClose();
    }
  };

  const labels = Array.isArray(form.labels) ? form.labels : [];
  const files = Array.isArray(form.files_involved) ? form.files_involved : [];
  const criteria = Array.isArray(form.acceptance_criteria) ? form.acceptance_criteria : [];
  const typeColor = TYPE_COLORS[form.type] || '#0078d4';

  return (
    <div className="detail-panel slide-in-right">
      {/* Header with type color bar */}
      <div className="detail-header">
        <div className="detail-header-bar" style={{ background: typeColor }} />
        <div className="detail-header-content">
          <div className="detail-header-left">
            <div className="detail-type-icon" style={{ background: typeColor }}>
              <svg width="12" height="12" viewBox="0 0 16 16" fill="white">
                <rect x="2" y="2" width="12" height="12" rx="2" />
              </svg>
            </div>
            <span className="detail-id">{task.id}</span>
          </div>
          <div className="detail-header-actions">
            <button className="btn btn-ghost" onClick={handleSave} disabled={saving} title="Save">
              <Save size={14} />
            </button>
            <button className="btn btn-ghost" onClick={handleDelete} title="Delete" style={{ color: 'var(--p0-color)' }}>
              <Trash2 size={14} />
            </button>
            <button className="btn btn-ghost" onClick={onClose} title="Close">
              <X size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="detail-body">
        {/* Title */}
        <input
          className="detail-title-input"
          value={form.title || ''}
          onChange={(e) => handleChange('title', e.target.value)}
          placeholder="Enter title"
        />

        {/* Fields grid */}
        <div className="detail-fields">
          <div className="detail-field">
            <label>Status</label>
            <select value={form.status} onChange={(e) => handleChange('status', e.target.value)}>
              {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABELS[s] || s}</option>)}
            </select>
          </div>

          <div className="detail-field">
            <label>Priority</label>
            <select value={form.priority} onChange={(e) => handleChange('priority', e.target.value)}>
              {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="detail-field">
            <label>Type</label>
            <select value={form.type} onChange={(e) => handleChange('type', e.target.value)}>
              {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          <div className="detail-field">
            <label>Assigned To</label>
            <AssigneeSelect
              value={form.assignee || ''}
              onChange={(val) => handleChange('assignee', val)}
            />
          </div>

          <div className="detail-field">
            <label>Due Date</label>
            <input
              type="date"
              value={form.due_date || ''}
              onChange={(e) => handleChange('due_date', e.target.value)}
            />
          </div>

          <div className="detail-field">
            <label>Effort (hrs)</label>
            <input
              type="number"
              value={form.estimated_hours || ''}
              onChange={(e) => handleChange('estimated_hours', e.target.value)}
              placeholder="0"
              step="0.5"
            />
          </div>
        </div>

        {/* Tags */}
        {labels.length > 0 && (
          <div className="detail-section">
            <label className="detail-section-label">Tags</label>
            <div className="card-labels" style={{ padding: '4px 0' }}>
              {labels.map((l) => <span key={l} className="label-chip">{l}</span>)}
            </div>
          </div>
        )}

        {/* Acceptance Criteria */}
        {criteria.length > 0 && (
          <div className="detail-section">
            <label className="detail-section-label">Acceptance Criteria</label>
            <ul className="detail-checklist">
              {criteria.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Files */}
        {files.length > 0 && (
          <div className="detail-section">
            <label className="detail-section-label">Related Files</label>
            <div className="detail-files">
              {files.map((f, i) => <code key={i}>{f}</code>)}
            </div>
          </div>
        )}

        {/* Verification */}
        {form.verification_command && (
          <div className="detail-section">
            <label className="detail-section-label">Verification Command</label>
            <code className="detail-verification-cmd">{form.verification_command}</code>
          </div>
        )}

        {/* Description */}
        <div className="detail-section">
          <label className="detail-section-label">Description</label>
          <textarea
            className="detail-description"
            value={form.body_markdown || ''}
            onChange={(e) => handleChange('body_markdown', e.target.value)}
            placeholder="Add a description..."
            rows={5}
          />
        </div>

        {/* Attachments */}
        <div className="detail-section">
          <label className="detail-section-label"><Paperclip size={11} /> Attachments</label>
          <div
            className={`attachment-dropzone ${dragOver ? 'drag-over' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(Array.from(e.dataTransfer.files)); }}
          >
            <span>{uploading ? 'Uploading...' : 'Drop files here or'}</span>
            <label className="attachment-browse">
              Browse
              <input type="file" multiple hidden onChange={(e) => { if (e.target.files.length) handleUpload(Array.from(e.target.files)); e.target.value = ''; }} />
            </label>
          </div>
          {attachments.length > 0 && (
            <div className="attachment-list">
              {attachments.map((a) => {
                const ext = (a.original_name || '').split('.').pop()?.toLowerCase();
                const isImage = IMAGE_EXTENSIONS.some((e) => a.original_name?.toLowerCase().endsWith(e));
                const fullUrl = `${UPLOADS_BASE}${a.url}`;
                return (
                  <div key={a.id} className="attachment-item">
                    {isImage ? (
                      <img className="attachment-thumb" src={fullUrl} alt={a.original_name} />
                    ) : (
                      <div className="attachment-icon"><FileText size={18} /></div>
                    )}
                    <div className="attachment-info">
                      <a href={fullUrl} target="_blank" rel="noreferrer" className="attachment-name">{a.original_name}</a>
                      <span className="attachment-meta">{formatBytes(a.size_bytes)} &middot; {a.uploaded_by_username}</span>
                    </div>
                    <button className="btn btn-ghost" onClick={() => handleDeleteAttachment(a.id)} title="Delete">
                      <X size={12} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Completion Notes */}
        {form.completion_notes && (
          <div className="detail-section">
            <label className="detail-section-label">Completion Notes</label>
            <div className="detail-completion">{form.completion_notes}</div>
          </div>
        )}

        {/* GitHub Links */}
        {links.length > 0 && (
          <div className="detail-section">
            <label className="detail-section-label">Linked PRs & Commits</label>
            <div className="task-links-list">
              {links.map((link) => (
                <a key={link.id} className="task-link-item" href={link.url} target="_blank" rel="noreferrer">
                  {link.link_type === 'pr' ? <GitPullRequest size={13} /> : <GitCommit size={13} />}
                  <span className="task-link-title">{link.title}</span>
                  <span className={`task-link-status task-link-status-${link.status}`}>{link.status}</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Time Tracking */}
        <div className="detail-section">
          <label className="detail-section-label"><Clock size={11} /> Time Tracking</label>
          {(() => {
            const totalLogged = timeEntries.reduce((sum, e) => sum + (e.hours || 0), 0);
            const estimated = form.estimated_hours || 0;
            const pct = estimated > 0 ? Math.min(100, (totalLogged / estimated) * 100) : 0;
            return (
              <>
                <div className="time-progress-row">
                  <span className="time-logged">{totalLogged.toFixed(1)}h logged</span>
                  {estimated > 0 && <span className="time-estimated">/ {estimated}h estimated</span>}
                </div>
                {estimated > 0 && (
                  <div className="time-bar-track">
                    <div className={`time-bar-fill ${pct >= 100 ? 'time-bar-over' : ''}`} style={{ width: `${pct}%` }} />
                  </div>
                )}
              </>
            );
          })()}
          <div className="time-log-form">
            <input
              type="number"
              placeholder="Hours"
              value={timeForm.hours}
              onChange={(e) => setTimeForm({ ...timeForm, hours: e.target.value })}
              step="0.25"
              min="0"
              className="time-hours-input"
            />
            <input
              placeholder="Description (optional)"
              value={timeForm.description}
              onChange={(e) => setTimeForm({ ...timeForm, description: e.target.value })}
              className="time-desc-input"
            />
            <button className="btn btn-ghost" onClick={handleLogTime} disabled={loggingTime || !timeForm.hours}>
              <Plus size={13} />
            </button>
          </div>
          {timeEntries.length > 0 && (
            <div className="time-entries">
              {timeEntries.slice(0, 5).map((e) => (
                <div key={e.id} className="time-entry">
                  <span className="time-entry-hours">{e.hours}h</span>
                  <span className="time-entry-desc">{e.description || '—'}</span>
                  <span className="time-entry-user">{e.username}</span>
                  <button className="btn btn-ghost time-entry-del" onClick={() => handleDeleteTime(e.id)}>
                    <X size={10} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tabs: Comments / Activity */}
        <div className="detail-tabs">
          <button
            className={`detail-tab ${activeTab === 'comments' ? 'active' : ''}`}
            onClick={() => setActiveTab('comments')}
          >
            <MessageSquare size={13} /> Comments ({comments.length})
          </button>
          <button
            className={`detail-tab ${activeTab === 'activity' ? 'active' : ''}`}
            onClick={() => setActiveTab('activity')}
          >
            <Activity size={13} /> Activity ({activities.length})
          </button>
        </div>

        {activeTab === 'comments' && (
          <div className="detail-tab-content">
            <div className="comment-input-row">
              <MentionInput
                value={commentText}
                onChange={setCommentText}
                onSubmit={handleAddComment}
                placeholder="Write a comment... (use @mention)"
                disabled={sendingComment}
              />
              <button className="btn btn-ghost" onClick={handleAddComment} disabled={sendingComment || !commentText.trim()}>
                <Send size={13} />
              </button>
            </div>
            {comments.length === 0 && <div className="tab-empty">No comments yet</div>}
            {comments.map((c) => (
              <div key={c.id} className="comment-item">
                <div className="comment-header">
                  <span className="comment-author">{c.username}</span>
                  <span className="comment-time">{new Date(c.created_at).toLocaleString()}</span>
                </div>
                <div className="comment-body">{
                  c.body.split(/(@\w+)/g).map((part, i) =>
                    part.startsWith('@') ? <span key={i} className="mention">{part}</span> : part
                  )
                }</div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="detail-tab-content">
            {activities.length === 0 && <div className="tab-empty">No activity yet</div>}
            {activities.map((a) => (
              <div key={a.id} className="activity-item">
                <div className="activity-dot" />
                <div className="activity-content">
                  <span className="activity-text">
                    <strong>{a.actor || 'system'}</strong>{' '}
                    {a.action === 'moved' && <>moved to <strong>{a.to_status}</strong></>}
                    {a.action === 'created' && 'created this task'}
                    {a.action === 'assigned' && `assigned to ${a.details ? JSON.parse(a.details).assignee : '—'}`}
                    {a.action === 'commented' && 'commented'}
                    {a.action === 'commit_linked' && `linked commit: ${a.details || ''}`}
                    {!['moved', 'created', 'assigned', 'commented', 'commit_linked'].includes(a.action) && a.action}
                  </span>
                  <span className="activity-time">{new Date(a.timestamp).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="detail-footer">
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          <Save size={13} /> {saving ? 'Saving...' : 'Save & Close'}
        </button>
      </div>
    </div>
  );
}
