import { useState, useEffect } from 'react';
import { X, Save, Trash2 } from 'lucide-react';
import { updateTask, deleteTask } from '../api';
import AssigneeSelect from './AssigneeSelect';
import './TaskDetail.css';

const STATUSES = ['backlog', 'in-progress', 'review', 'done', 'blocked'];
const PRIORITIES = ['P0', 'P1', 'P2', 'P3'];
const TYPES = ['feature', 'bug', 'tech-debt', 'research', 'ops'];
const STATUS_LABELS = { backlog: 'New', 'in-progress': 'Active', review: 'Resolved', done: 'Closed', blocked: 'Blocked' };
const TYPE_COLORS = { feature: '#773b93', bug: '#cc293d', 'tech-debt': '#ca5010', research: '#0078d4', ops: '#8a8886' };

export default function TaskDetail({ task, onClose, onUpdate }) {
  const [form, setForm] = useState({ ...task });
  const [saving, setSaving] = useState(false);

  useEffect(() => { setForm({ ...task }); }, [task]);
  if (!task) return null;

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

        {/* Completion Notes */}
        {form.completion_notes && (
          <div className="detail-section">
            <label className="detail-section-label">Completion Notes</label>
            <div className="detail-completion">{form.completion_notes}</div>
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
