import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { createTask, getTemplates, decomposeEpic } from '../api';
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
  const [templates, setTemplates] = useState([]);
  const [decomposing, setDecomposing] = useState(false);
  const [decomposed, setDecomposed] = useState(null);
  const [creatingAll, setCreatingAll] = useState(false);

  useEffect(() => {
    getTemplates().then(setTemplates).catch(() => {});
  }, []);

  const applyTemplate = (tpl) => {
    setForm({
      ...form,
      type: tpl.type || form.type,
      priority: tpl.priority || form.priority,
      labels: tpl.labels ? (Array.isArray(tpl.labels) ? tpl.labels.join(', ') : tpl.labels) : form.labels,
      body_markdown: tpl.body_markdown || form.body_markdown,
    });
  };

  const handleDecompose = async () => {
    if (!form.title.trim()) return;
    setDecomposing(true);
    try {
      const result = await decomposeEpic({
        title: form.title,
        description: form.body_markdown || '',
        type: form.type,
        estimated_hours: null,
        assignee: form.assignee || null,
      });
      setDecomposed(result);
    } catch (e) {
      console.error(e);
    }
    setDecomposing(false);
  };

  const handleCreateAll = async () => {
    if (!decomposed) return;
    setCreatingAll(true);
    try {
      await createTask({
        ...form,
        labels: form.labels ? form.labels.split(',').map((l) => l.trim()).filter(Boolean) : [],
        assignee: form.assignee || null,
      });
      for (const sub of decomposed.suggested_subtasks) {
        await createTask(sub);
      }
      onCreated?.();
      onClose();
    } catch (e) {
      console.error(e);
    }
    setCreatingAll(false);
  };

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
          {templates.length > 0 && (
            <div className="form-group">
              <label>Use Template</label>
              <select
                onChange={(e) => {
                  const tpl = templates.find((t) => String(t.id) === e.target.value);
                  if (tpl) applyTemplate(tpl);
                }}
                defaultValue=""
              >
                <option value="">— None —</option>
                {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
          )}
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
          {decomposed && (
            <div style={{ marginTop: 16, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>
                  {decomposed.suggested_subtasks.length} suggested subtasks
                  &nbsp;({decomposed.total_estimated_hours}h total)
                </span>
                <button type="button" className="btn btn-primary btn-sm" onClick={handleCreateAll} disabled={creatingAll}>
                  {creatingAll ? 'Creating...' : 'Create All'}
                </button>
              </div>
              {decomposed.suggested_subtasks.map((s, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0',
                  borderBottom: '1px solid var(--border-light, var(--border))', fontSize: 12
                }}>
                  <span style={{ color: 'var(--text-muted)', width: 20 }}>{i + 1}.</span>
                  <span style={{ flex: 1 }}>{s.title}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{s.type}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{s.estimated_hours}h</span>
                </div>
              ))}
            </div>
          )}
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={handleDecompose} disabled={decomposing || !form.title.trim()}>
              {decomposing ? 'Decomposing...' : 'Decompose Epic'}
            </button>
            <div style={{ flex: 1 }} />
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
