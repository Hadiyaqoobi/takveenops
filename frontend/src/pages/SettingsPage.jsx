import { useState, useEffect } from 'react';
import { Settings, Plus, Trash2, Bot, User, Github, Link2, Unlink, FileText, Repeat, Webhook, Play, Zap, Mail, Send, RefreshCw, X, Check, Clock } from 'lucide-react';
import {
  getTeam, addTeamMember, deleteTeamMember, getSprints, createSprint,
  getGitHubConfig, setupGitHub, disconnectGitHub,
  getTemplates, createTemplate, deleteTemplate,
  getRecurringRules, createRecurringRule, deleteRecurringRule, runRecurringRules,
  getWebhooks, createWebhook, deleteWebhook, testWebhook,
  sendInvitation, getInvitations, revokeInvitation, resendInvitation,
} from '../api';
import './SettingsPage.css';

export default function SettingsPage() {
  const [team, setTeam] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [newMember, setNewMember] = useState({ id: '', name: '', type: 'human', role: 'engineer' });
  const [newSprint, setNewSprint] = useState({ name: '', goal: '', start_date: '', end_date: '' });
  const [ghConfig, setGhConfig] = useState(null);
  const [ghForm, setGhForm] = useState({ repo_owner: '', repo_name: '', access_token: '', webhook_secret: '' });
  const [ghLoading, setGhLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [newTemplate, setNewTemplate] = useState({ name: '', type: 'feature', priority: 'P2', labels: '', body_markdown: '' });
  const [recurring, setRecurring] = useState([]);
  const [newRule, setNewRule] = useState({ title: '', type: 'feature', priority: 'P2', frequency: 'weekly', assignee: '' });
  const [webhooks, setWebhooks] = useState([]);
  const [newWebhook, setNewWebhook] = useState({ name: '', url: '', events: '' });
  const [invitations, setInvitations] = useState([]);
  const [inviteForm, setInviteForm] = useState({ email: '', role: 'member' });
  const [inviteMsg, setInviteMsg] = useState('');
  const [inviteLoading, setInviteLoading] = useState(false);

  const loadTeam = async () => {
    try { setTeam(await getTeam()); } catch (e) { console.error(e); }
  };
  const loadSprints = async () => {
    try { setSprints(await getSprints()); } catch (e) { console.error(e); }
  };
  const loadGhConfig = async () => {
    try { setGhConfig(await getGitHubConfig()); } catch (e) { console.error(e); }
  };
  const loadTemplates = async () => {
    try { setTemplates(await getTemplates()); } catch (e) { console.error(e); }
  };
  const loadRecurring = async () => {
    try { setRecurring(await getRecurringRules()); } catch (e) { console.error(e); }
  };
  const loadWebhooks = async () => {
    try { setWebhooks(await getWebhooks()); } catch (e) { console.error(e); }
  };
  const loadInvitations = async () => {
    try { setInvitations(await getInvitations()); } catch (e) { console.error(e); }
  };

  useEffect(() => { loadTeam(); loadSprints(); loadGhConfig(); loadTemplates(); loadRecurring(); loadWebhooks(); loadInvitations(); }, []);

  const handleGhSetup = async (e) => {
    e.preventDefault();
    if (!ghForm.repo_owner || !ghForm.repo_name || !ghForm.access_token) return;
    setGhLoading(true);
    try {
      await setupGitHub(ghForm);
      setGhForm({ repo_owner: '', repo_name: '', access_token: '', webhook_secret: '' });
      loadGhConfig();
    } catch (e) { console.error(e); }
    setGhLoading(false);
  };

  const handleGhDisconnect = async () => {
    if (!window.confirm('Disconnect GitHub?')) return;
    try { await disconnectGitHub(); loadGhConfig(); } catch (e) { console.error(e); }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!newMember.id || !newMember.name) return;
    try {
      await addTeamMember(newMember);
      setNewMember({ id: '', name: '', type: 'human', role: 'engineer' });
      loadTeam();
    } catch (e) { console.error(e); }
  };

  const handleDeleteMember = async (id) => {
    if (!window.confirm(`Remove ${id}?`)) return;
    try { await deleteTeamMember(id); loadTeam(); } catch (e) { console.error(e); }
  };

  const handleCreateSprint = async (e) => {
    e.preventDefault();
    if (!newSprint.name) return;
    try {
      await createSprint(newSprint);
      setNewSprint({ name: '', goal: '', start_date: '', end_date: '' });
      loadSprints();
    } catch (e) { console.error(e); }
  };

  return (
    <>
      <div className="page-header">
        <h1><Settings size={16} /> Settings</h1>
      </div>

      <div className="page-body">
        <div className="settings-grid">
          {/* Invite Users */}
          <div className="settings-card">
            <h3><Mail size={16} /> Invite Users</h3>
            <div className="team-list">
              {invitations.map((inv) => (
                <div key={inv.id} className="team-row">
                  <div className="team-avatar">
                    {inv.status === 'pending' ? <Clock size={14} /> : inv.status === 'accepted' ? <Check size={14} /> : <X size={14} />}
                  </div>
                  <div className="team-info">
                    <div className="team-name">{inv.email}</div>
                    <div className="team-role">
                      {inv.status} &middot; invited by {inv.invited_by} &middot; {inv.role}
                    </div>
                  </div>
                  {inv.status === 'pending' && (
                    <>
                      <button className="btn btn-ghost" title="Resend" onClick={async () => {
                        try { await resendInvitation(inv.id); alert('Invitation resent!'); } catch (e) { alert(e.message); }
                      }}>
                        <RefreshCw size={13} />
                      </button>
                      <button className="btn btn-ghost" title="Revoke" onClick={async () => {
                        if (!window.confirm(`Revoke invitation for ${inv.email}?`)) return;
                        await revokeInvitation(inv.id);
                        loadInvitations();
                      }}>
                        <Trash2 size={13} />
                      </button>
                    </>
                  )}
                </div>
              ))}
              {invitations.length === 0 && <div className="standup-empty">No invitations sent yet</div>}
            </div>

            <form className="settings-form" onSubmit={async (e) => {
              e.preventDefault();
              if (!inviteForm.email) return;
              setInviteLoading(true);
              setInviteMsg('');
              try {
                const res = await sendInvitation(inviteForm);
                setInviteMsg(res.message || 'Invitation sent!');
                setInviteForm({ email: '', role: 'member' });
                loadInvitations();
              } catch (err) {
                setInviteMsg(err.message || 'Failed to send invitation');
              }
              setInviteLoading(false);
            }}>
              <h4>Send Invitation</h4>
              <input
                type="email"
                placeholder="Email address"
                value={inviteForm.email}
                onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                required
              />
              <div className="form-row">
                <select value={inviteForm.role} onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}>
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </select>
                <button type="submit" className="btn btn-primary" disabled={inviteLoading}>
                  <Send size={14} /> {inviteLoading ? 'Sending...' : 'Invite'}
                </button>
              </div>
              {inviteMsg && <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{inviteMsg}</div>}
            </form>
          </div>

          {/* Team */}
          <div className="settings-card">
            <h3>Team Members</h3>
            <div className="team-list">
              {team.map((m) => (
                <div key={m.id} className="team-row">
                  <div className="team-avatar">
                    {m.type === 'ai-agent' ? <Bot size={14} /> : <User size={14} />}
                  </div>
                  <div className="team-info">
                    <div className="team-name">{m.name}</div>
                    <div className="team-role">{m.role} / {m.type}</div>
                  </div>
                  <button className="btn btn-ghost" onClick={() => handleDeleteMember(m.id)}>
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>

            <form className="settings-form" onSubmit={handleAddMember}>
              <h4>Add Team Member</h4>
              <div className="form-row">
                <input placeholder="ID" value={newMember.id} onChange={(e) => setNewMember({ ...newMember, id: e.target.value })} />
                <input placeholder="Name" value={newMember.name} onChange={(e) => setNewMember({ ...newMember, name: e.target.value })} />
              </div>
              <div className="form-row">
                <select value={newMember.type} onChange={(e) => setNewMember({ ...newMember, type: e.target.value })}>
                  <option value="human">Human</option>
                  <option value="ai-agent">AI Agent</option>
                </select>
                <select value={newMember.role} onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}>
                  <option value="founder">Founder</option>
                  <option value="engineer">Engineer</option>
                  <option value="ai-agent">AI Agent</option>
                  <option value="reviewer">Reviewer</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary"><Plus size={14} /> Add</button>
            </form>
          </div>

          {/* Sprints */}
          <div className="settings-card">
            <h3>Sprints</h3>
            <div className="sprint-list">
              {sprints.map((s) => (
                <div key={s.id} className="sprint-row">
                  <div className="sprint-name">{s.name}</div>
                  <div className="sprint-dates">
                    {s.start_date || '—'} to {s.end_date || '—'}
                  </div>
                  <span className={`badge badge-${s.status === 'active' ? 'p2' : 'p3'}`}>{s.status}</span>
                </div>
              ))}
              {sprints.length === 0 && <div className="standup-empty">No sprints yet</div>}
            </div>

            <form className="settings-form" onSubmit={handleCreateSprint}>
              <h4>Create Sprint</h4>
              <input placeholder="Sprint name" value={newSprint.name} onChange={(e) => setNewSprint({ ...newSprint, name: e.target.value })} />
              <input placeholder="Goal" value={newSprint.goal} onChange={(e) => setNewSprint({ ...newSprint, goal: e.target.value })} />
              <div className="form-row">
                <input type="date" value={newSprint.start_date} onChange={(e) => setNewSprint({ ...newSprint, start_date: e.target.value })} />
                <input type="date" value={newSprint.end_date} onChange={(e) => setNewSprint({ ...newSprint, end_date: e.target.value })} />
              </div>
              <button type="submit" className="btn btn-primary"><Plus size={14} /> Create Sprint</button>
            </form>
          </div>
          {/* Templates */}
          <div className="settings-card">
            <h3><FileText size={16} /> Task Templates</h3>
            <div className="team-list">
              {templates.map((t) => (
                <div key={t.id} className="team-row">
                  <div className="team-info">
                    <div className="team-name">{t.name}</div>
                    <div className="team-role">{t.type} / {t.priority}</div>
                  </div>
                  <button className="btn btn-ghost" onClick={async () => { await deleteTemplate(t.id); loadTemplates(); }}>
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              {templates.length === 0 && <div className="standup-empty">No templates</div>}
            </div>
            <form className="settings-form" onSubmit={async (e) => {
              e.preventDefault();
              if (!newTemplate.name) return;
              await createTemplate({ ...newTemplate, labels: newTemplate.labels ? newTemplate.labels.split(',').map((l) => l.trim()) : [] });
              setNewTemplate({ name: '', type: 'feature', priority: 'P2', labels: '', body_markdown: '' });
              loadTemplates();
            }}>
              <h4>Add Template</h4>
              <input placeholder="Template name" value={newTemplate.name} onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })} />
              <div className="form-row">
                <select value={newTemplate.type} onChange={(e) => setNewTemplate({ ...newTemplate, type: e.target.value })}>
                  <option value="feature">Feature</option>
                  <option value="bug">Bug</option>
                  <option value="tech-debt">Tech Debt</option>
                  <option value="research">Research</option>
                  <option value="ops">Ops</option>
                </select>
                <select value={newTemplate.priority} onChange={(e) => setNewTemplate({ ...newTemplate, priority: e.target.value })}>
                  <option value="P0">P0</option>
                  <option value="P1">P1</option>
                  <option value="P2">P2</option>
                  <option value="P3">P3</option>
                </select>
              </div>
              <input placeholder="Labels (comma-separated)" value={newTemplate.labels} onChange={(e) => setNewTemplate({ ...newTemplate, labels: e.target.value })} />
              <textarea placeholder="Description template" value={newTemplate.body_markdown} onChange={(e) => setNewTemplate({ ...newTemplate, body_markdown: e.target.value })} rows={2} />
              <button type="submit" className="btn btn-primary"><Plus size={14} /> Add Template</button>
            </form>
          </div>

          {/* Recurring */}
          <div className="settings-card">
            <h3><Repeat size={16} /> Recurring Tasks</h3>
            <div className="team-list">
              {recurring.map((r) => (
                <div key={r.id} className="team-row">
                  <div className="team-info">
                    <div className="team-name">{r.title}</div>
                    <div className="team-role">{r.frequency} / next: {r.next_run || '—'} / {r.active ? 'active' : 'paused'}</div>
                  </div>
                  <button className="btn btn-ghost" onClick={async () => { await deleteRecurringRule(r.id); loadRecurring(); }}>
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              {recurring.length === 0 && <div className="standup-empty">No recurring rules</div>}
            </div>
            <form className="settings-form" onSubmit={async (e) => {
              e.preventDefault();
              if (!newRule.title) return;
              await createRecurringRule(newRule);
              setNewRule({ title: '', type: 'feature', priority: 'P2', frequency: 'weekly', assignee: '' });
              loadRecurring();
            }}>
              <h4>Add Recurring Rule</h4>
              <input placeholder="Task title" value={newRule.title} onChange={(e) => setNewRule({ ...newRule, title: e.target.value })} />
              <div className="form-row">
                <select value={newRule.frequency} onChange={(e) => setNewRule({ ...newRule, frequency: e.target.value })}>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Biweekly</option>
                  <option value="monthly">Monthly</option>
                </select>
                <input placeholder="Assignee" value={newRule.assignee} onChange={(e) => setNewRule({ ...newRule, assignee: e.target.value })} />
              </div>
              <button type="submit" className="btn btn-primary"><Plus size={14} /> Add Rule</button>
            </form>
            <button className="btn btn-ghost" onClick={async () => {
              const res = await runRecurringRules();
              alert(`Created ${res.created?.length || 0} task(s)`);
              loadRecurring();
            }} style={{ marginTop: 8 }}>
              <Play size={13} /> Run Due Rules Now
            </button>
          </div>

          {/* Webhooks */}
          <div className="settings-card">
            <h3><Webhook size={16} /> Webhooks</h3>
            <div className="team-list">
              {webhooks.map((w) => (
                <div key={w.id} className="team-row">
                  <div className="team-info">
                    <div className="team-name">{w.name}</div>
                    <div className="team-role">{w.url}</div>
                  </div>
                  <button className="btn btn-ghost" title="Test" onClick={async () => {
                    const res = await testWebhook(w.id);
                    alert(res.success ? 'Webhook test sent!' : 'Webhook test failed');
                  }}>
                    <Zap size={13} />
                  </button>
                  <button className="btn btn-ghost" onClick={async () => { await deleteWebhook(w.id); loadWebhooks(); }}>
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              {webhooks.length === 0 && <div className="standup-empty">No webhooks configured</div>}
            </div>
            <form className="settings-form" onSubmit={async (e) => {
              e.preventDefault();
              if (!newWebhook.name || !newWebhook.url) return;
              await createWebhook({
                ...newWebhook,
                events: newWebhook.events ? newWebhook.events.split(',').map((e) => e.trim()) : [],
              });
              setNewWebhook({ name: '', url: '', events: '' });
              loadWebhooks();
            }}>
              <h4>Add Webhook</h4>
              <input placeholder="Name" value={newWebhook.name} onChange={(e) => setNewWebhook({ ...newWebhook, name: e.target.value })} />
              <input placeholder="URL" value={newWebhook.url} onChange={(e) => setNewWebhook({ ...newWebhook, url: e.target.value })} />
              <input placeholder="Events (comma-separated, leave empty for all)" value={newWebhook.events} onChange={(e) => setNewWebhook({ ...newWebhook, events: e.target.value })} />
              <button type="submit" className="btn btn-primary"><Plus size={14} /> Add Webhook</button>
            </form>
          </div>

          {/* GitHub Integration */}
          <div className="settings-card">
            <h3><Github size={16} /> GitHub Integration</h3>
            {ghConfig?.connected ? (
              <div className="gh-connected">
                <div className="gh-repo-info">
                  <Link2 size={14} />
                  <span>Connected to <strong>{ghConfig.repo_owner}/{ghConfig.repo_name}</strong></span>
                </div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '8px 0' }}>
                  PRs and commits mentioning task IDs (e.g. ROE-001) will auto-link and update task status.
                </p>
                <button className="btn btn-ghost" onClick={handleGhDisconnect} style={{ color: '#cc293d' }}>
                  <Unlink size={13} /> Disconnect
                </button>
              </div>
            ) : (
              <form className="settings-form" onSubmit={handleGhSetup}>
                <h4>Connect Repository</h4>
                <div className="form-row">
                  <input placeholder="Owner" value={ghForm.repo_owner} onChange={(e) => setGhForm({ ...ghForm, repo_owner: e.target.value })} />
                  <input placeholder="Repo name" value={ghForm.repo_name} onChange={(e) => setGhForm({ ...ghForm, repo_name: e.target.value })} />
                </div>
                <input placeholder="Personal access token" type="password" value={ghForm.access_token} onChange={(e) => setGhForm({ ...ghForm, access_token: e.target.value })} />
                <input placeholder="Webhook secret (optional)" value={ghForm.webhook_secret} onChange={(e) => setGhForm({ ...ghForm, webhook_secret: e.target.value })} />
                <button type="submit" className="btn btn-primary" disabled={ghLoading}>
                  <Link2 size={14} /> {ghLoading ? 'Connecting...' : 'Connect'}
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
