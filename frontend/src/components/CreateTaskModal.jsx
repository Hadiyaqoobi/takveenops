import { useState } from 'react';
import { X } from 'lucide-react';
import { createTask } from '../api';
import AssigneeSelect from './AssigneeSelect';
import './CreateTaskModal.css';

const TYPES = ['feature', 'bug', 'tech-debt', 'research', 'ops'];
const PRIORITIES = ['P0', 'P1', 'P2', 'P3'];

export default function CreateTaskModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    title: '',
    type: 'feature',
    priority: 'P2',
    assignee: '',
    labels: '',
    body_markdown: '',
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      await createTask({
        ...form,
        labels: form.labels ? form.labels.split(',').map((l) => l.trim()).filter(Boolean) : [],
        assignee: form.assignee || null,
      });
      onCreated?.();
      onClose();
    } catch (e) {
      console.error(e);
    }
    setSaving(false);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>New Task</h2>
          <button className="btn btn-ghost" onClick={onClose}><X size={16} /></button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label>Title</label>
            <input
              autoFocus
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Task title..."
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Type</label>
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Priority</label>
              <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
                {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Assignee</label>
            <AssigneeSelect
              value={form.assignee}
              onChange={(val) => setForm({ ...form, assignee: val || '' })}
            />
          </div>
          <div className="form-group">
            <label>Labels (comma-separated)</label>
            <input
              value={form.labels}
              onChange={(e) => setForm({ ...form, labels: e.target.value })}
              placeholder="e.g. ml, api, frontend"
            />
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea
              value={form.body_markdown}
              onChange={(e) => setForm({ ...form, body_markdown: e.target.value })}
              placeholder="Task details..."
              rows={4}
            />
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={saving || !form.title.trim()}>
              {saving ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
