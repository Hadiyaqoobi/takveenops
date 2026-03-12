import { useState, useEffect } from 'react';
import { Settings, Plus, Trash2, Bot, User } from 'lucide-react';
import { getTeam, addTeamMember, deleteTeamMember, getSprints, createSprint } from '../api';
import './SettingsPage.css';

export default function SettingsPage() {
  const [team, setTeam] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [newMember, setNewMember] = useState({ id: '', name: '', type: 'human', role: 'engineer' });
  const [newSprint, setNewSprint] = useState({ name: '', goal: '', start_date: '', end_date: '' });

  const loadTeam = async () => {
    try { setTeam(await getTeam()); } catch (e) { console.error(e); }
  };
  const loadSprints = async () => {
    try { setSprints(await getSprints()); } catch (e) { console.error(e); }
  };

  useEffect(() => { loadTeam(); loadSprints(); }, []);

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
        </div>
      </div>
    </>
  );
}
