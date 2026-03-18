import { useState, useEffect, useRef } from 'react';
import {
  Mic, MicOff, RefreshCw, CheckCircle, Clock, Eye, AlertOctagon, AlertTriangle,
  Sparkles, Copy, Check, Send, Users, Bell, Plus, X, ChevronDown, ChevronRight,
  Calendar, Trash2, Edit3, Save,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import {
  getStandup, getAiStandup, getMyChecklist, submitStandup,
  getStandupEntries, sendStandupReminders,
  getStandupMeetings, createStandupMeeting, updateStandupMeeting, deleteStandupMeeting,
  getTeam,
} from '../api';
import './StandupPage.css';

export default function StandupPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState('my-standup');

  // Overview state
  const [standup, setStandup] = useState(null);
  const [loading, setLoading] = useState(false);

  // AI standup
  const [aiStandup, setAiStandup] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // My standup checklist
  const [checklist, setChecklist] = useState(null);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const [yesterdayItems, setYesterdayItems] = useState([]);
  const [todayItems, setTodayItems] = useState([]);
  const [blockerItems, setBlockerItems] = useState([]);
  const [extraNotes, setExtraNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [newYesterday, setNewYesterday] = useState('');
  const [newToday, setNewToday] = useState('');
  const [newBlocker, setNewBlocker] = useState('');

  // Voice recording
  const [recording, setRecording] = useState(false);
  const [audioURL, setAudioURL] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorder = useRef(null);
  const audioChunks = useRef([]);
  const recognitionRef = useRef(null);

  // Team entries
  const [teamEntries, setTeamEntries] = useState([]);
  const [teamLoading, setTeamLoading] = useState(false);
  const [reminding, setReminding] = useState(false);
  const [reminded, setReminded] = useState(false);

  // Meetings
  const [meetings, setMeetings] = useState([]);
  const [meetingsLoading, setMeetingsLoading] = useState(false);
  const [showMeetingForm, setShowMeetingForm] = useState(false);
  const [editingMeeting, setEditingMeeting] = useState(null);
  const [meetingForm, setMeetingForm] = useState({ title: '', scheduled_time: '09:00', frequency: 'daily', participants: [], notes: '' });
  const [teamMembers, setTeamMembers] = useState([]);

  // Load overview
  const loadOverview = async () => {
    setLoading(true);
    try { setStandup(await getStandup()); } catch (e) { console.error(e); }
    setLoading(false);
  };

  // Load AI standup
  const loadAi = async () => {
    setAiLoading(true);
    try { setAiStandup(await getAiStandup()); } catch (e) { console.error(e); }
    setAiLoading(false);
  };

  const handleCopy = () => {
    if (aiStandup?.summary_text) {
      navigator.clipboard.writeText(aiStandup.summary_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Load my checklist
  const loadChecklist = async () => {
    setChecklistLoading(true);
    try {
      const data = await getMyChecklist();
      setChecklist(data);
      setYesterdayItems(data.yesterday || []);
      setTodayItems(data.today || []);
      setBlockerItems(data.blockers || []);
      setSubmitted(false);
    } catch (e) { console.error(e); }
    setChecklistLoading(false);
  };

  // Submit standup
  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const yesterday = yesterdayItems.filter((i) => i.checked).map((i) => i.text);
      const today = todayItems.filter((i) => i.checked).map((i) => i.text);
      const blockers = blockerItems.filter((i) => i.checked).map((i) => i.text);
      await submitStandup({ yesterday, today, blockers, notes: extraNotes, audio_transcript: transcript });
      setSubmitted(true);
    } catch (e) { console.error(e); }
    setSubmitting(false);
  };

  // Toggle item
  const toggleItem = (list, setList, index) => {
    const updated = [...list];
    updated[index] = { ...updated[index], checked: !updated[index].checked };
    setList(updated);
  };

  // Add custom item
  const addItem = (list, setList, text, setText) => {
    if (!text.trim()) return;
    setList([...list, { text: text.trim(), task_id: null, checked: true }]);
    setText('');
  };

  // Remove item
  const removeItem = (list, setList, index) => {
    setList(list.filter((_, i) => i !== index));
  };

  // Voice recording with Web Speech API
  const startRecording = () => {
    // Use Web Speech API for live transcription
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Try Chrome or Edge.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    let finalTranscript = '';

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      setTranscript(finalTranscript + interim);
    };

    recognition.onerror = (e) => {
      console.error('Speech recognition error:', e.error);
      setRecording(false);
    };

    recognition.onend = () => {
      setRecording(false);
      setTranscript(finalTranscript.trim());
    };

    recognitionRef.current = recognition;
    recognition.start();
    setRecording(true);
    setTranscript('');
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setRecording(false);
  };

  // Parse transcript into checklist items
  const parseTranscript = () => {
    if (!transcript.trim()) return;
    // Simple heuristic: split by sentences/periods
    const sentences = transcript.split(/[.!?]+/).map((s) => s.trim()).filter((s) => s.length > 3);

    // Categorize by keywords
    let section = 'yesterday';
    for (const s of sentences) {
      const lower = s.toLowerCase();
      if (lower.includes('today') || lower.includes('going to') || lower.includes('plan to') || lower.includes('will ')) {
        section = 'today';
      } else if (lower.includes('block') || lower.includes('stuck') || lower.includes('issue') || lower.includes('problem')) {
        section = 'blockers';
      }

      const item = { text: s, task_id: null, checked: true };
      if (section === 'yesterday') {
        setYesterdayItems((prev) => [...prev, item]);
      } else if (section === 'today') {
        setTodayItems((prev) => [...prev, item]);
      } else {
        setBlockerItems((prev) => [...prev, item]);
      }
    }
    setTranscript('');
  };

  // Load team entries
  const loadTeamEntries = async () => {
    setTeamLoading(true);
    try { setTeamEntries(await getStandupEntries()); } catch (e) { console.error(e); }
    setTeamLoading(false);
  };

  // Send reminders
  const handleRemind = async () => {
    setReminding(true);
    try {
      await sendStandupReminders();
      setReminded(true);
      setTimeout(() => setReminded(false), 3000);
    } catch (e) { console.error(e); }
    setReminding(false);
  };

  // Load meetings
  const loadMeetings = async () => {
    setMeetingsLoading(true);
    try {
      const [m, t] = await Promise.all([getStandupMeetings(), getTeam()]);
      setMeetings(m);
      setTeamMembers(t);
    } catch (e) { console.error(e); }
    setMeetingsLoading(false);
  };

  const openMeetingForm = (meeting = null) => {
    if (meeting) {
      setEditingMeeting(meeting);
      setMeetingForm({ title: meeting.title, scheduled_time: meeting.scheduled_time, frequency: meeting.frequency, participants: meeting.participants || [], notes: meeting.notes || '' });
    } else {
      setEditingMeeting(null);
      setMeetingForm({ title: '', scheduled_time: '09:00', frequency: 'daily', participants: [], notes: '' });
    }
    setShowMeetingForm(true);
  };

  const handleSaveMeeting = async () => {
    if (!meetingForm.title.trim()) return;
    try {
      if (editingMeeting) {
        await updateStandupMeeting(editingMeeting.id, meetingForm);
      } else {
        await createStandupMeeting(meetingForm);
      }
      setShowMeetingForm(false);
      loadMeetings();
    } catch (e) { console.error(e); }
  };

  const handleDeleteMeeting = async (id) => {
    if (!window.confirm('Delete this standup meeting?')) return;
    try {
      await deleteStandupMeeting(id);
      loadMeetings();
    } catch (e) { console.error(e); }
  };

  const toggleParticipant = (memberId) => {
    setMeetingForm((f) => ({
      ...f,
      participants: f.participants.includes(memberId)
        ? f.participants.filter((p) => p !== memberId)
        : [...f.participants, memberId],
    }));
  };

  // Initial load based on tab
  useEffect(() => {
    if (tab === 'overview' && !standup) loadOverview();
    if (tab === 'my-standup' && !checklist) loadChecklist();
    if (tab === 'ai' && !aiStandup) loadAi();
    if (tab === 'team' && teamEntries.length === 0) loadTeamEntries();
    if (tab === 'meetings' && meetings.length === 0) loadMeetings();
  }, [tab]);

  return (
    <>
      <div className="page-header">
        <h1><Mic size={16} /> Daily Standup</h1>
        <div className="page-header-actions">
          <button className="btn btn-secondary" onClick={() => {
            if (tab === 'my-standup') loadChecklist();
            else if (tab === 'overview') loadOverview();
            else if (tab === 'ai') loadAi();
            else if (tab === 'team') loadTeamEntries();
            else if (tab === 'meetings') loadMeetings();
          }}>
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      <div className="standup-tabs">
        <button className={`standup-tab ${tab === 'my-standup' ? 'active' : ''}`} onClick={() => setTab('my-standup')}>
          <CheckCircle size={13} /> My Standup
        </button>
        <button className={`standup-tab ${tab === 'team' ? 'active' : ''}`} onClick={() => setTab('team')}>
          <Users size={13} /> Team
        </button>
        <button className={`standup-tab ${tab === 'overview' ? 'active' : ''}`} onClick={() => setTab('overview')}>
          Overview
        </button>
        <button className={`standup-tab ${tab === 'meetings' ? 'active' : ''}`} onClick={() => setTab('meetings')}>
          <Calendar size={13} /> Meetings
        </button>
        <button className={`standup-tab ${tab === 'ai' ? 'active' : ''}`} onClick={() => setTab('ai')}>
          <Sparkles size={13} /> AI Standup
        </button>
      </div>

      <div className="page-body">
        {/* ── My Standup (Checklist + Voice) ── */}
        {tab === 'my-standup' && (
          <div className="my-standup-section fade-in">
            {checklistLoading && <div className="standup-loading">Loading your standup...</div>}

            {submitted && (
              <div className="standup-success">
                <CheckCircle size={18} />
                <span>Standup submitted for {checklist?.date}!</span>
              </div>
            )}

            {checklist && !checklistLoading && !submitted && (
              <>
                <div className="standup-checklist-header">
                  <h3>Standup for {checklist.date}</h3>
                  <span className="standup-user-badge">{user?.display_name || user?.username}</span>
                </div>

                {/* Voice Recording */}
                <div className="voice-section">
                  <div className="voice-controls">
                    {recording ? (
                      <button className="btn btn-primary voice-btn recording" onClick={stopRecording}>
                        <MicOff size={14} /> Stop Recording
                      </button>
                    ) : (
                      <button className="btn btn-secondary voice-btn" onClick={startRecording}>
                        <Mic size={14} /> Record Voice Standup
                      </button>
                    )}
                    {recording && <span className="voice-indicator">Listening...</span>}
                  </div>
                  {transcript && (
                    <div className="voice-transcript">
                      <div className="voice-transcript-header">
                        <span className="voice-transcript-label">Transcript</span>
                        <button className="btn btn-ghost" onClick={parseTranscript} title="Add to checklist">
                          <Plus size={12} /> Add to checklist
                        </button>
                        <button className="btn btn-ghost" onClick={() => setTranscript('')}>
                          <X size={12} />
                        </button>
                      </div>
                      <p>{transcript}</p>
                    </div>
                  )}
                </div>

                {/* Yesterday */}
                <ChecklistSection
                  title="What I did yesterday"
                  icon={<CheckCircle size={13} />}
                  items={yesterdayItems}
                  onToggle={(i) => toggleItem(yesterdayItems, setYesterdayItems, i)}
                  onRemove={(i) => removeItem(yesterdayItems, setYesterdayItems, i)}
                  newValue={newYesterday}
                  onNewChange={setNewYesterday}
                  onAdd={() => addItem(yesterdayItems, setYesterdayItems, newYesterday, setNewYesterday)}
                  placeholder="Add an item..."
                  emptyText="No activity detected yesterday"
                />

                {/* Today */}
                <ChecklistSection
                  title="What I'm doing today"
                  icon={<Clock size={13} />}
                  items={todayItems}
                  onToggle={(i) => toggleItem(todayItems, setTodayItems, i)}
                  onRemove={(i) => removeItem(todayItems, setTodayItems, i)}
                  newValue={newToday}
                  onNewChange={setNewToday}
                  onAdd={() => addItem(todayItems, setTodayItems, newToday, setNewToday)}
                  placeholder="Add a plan..."
                  emptyText="No in-progress tasks"
                />

                {/* Blockers */}
                <ChecklistSection
                  title="Blockers"
                  icon={<AlertOctagon size={13} />}
                  items={blockerItems}
                  onToggle={(i) => toggleItem(blockerItems, setBlockerItems, i)}
                  onRemove={(i) => removeItem(blockerItems, setBlockerItems, i)}
                  newValue={newBlocker}
                  onNewChange={setNewBlocker}
                  onAdd={() => addItem(blockerItems, setBlockerItems, newBlocker, setNewBlocker)}
                  placeholder="Add a blocker..."
                  emptyText="No blockers"
                  variant="blockers"
                />

                {/* Extra notes */}
                <div className="standup-notes-section">
                  <label>Additional Notes</label>
                  <textarea
                    value={extraNotes}
                    onChange={(e) => setExtraNotes(e.target.value)}
                    placeholder="Anything else to share..."
                    rows={2}
                  />
                </div>

                {/* Submit */}
                <div className="standup-submit-row">
                  <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                    <Send size={13} /> {submitting ? 'Submitting...' : 'Submit Standup'}
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Team Entries ── */}
        {tab === 'team' && (
          <div className="team-standup-section fade-in" style={{ maxWidth: 720 }}>
            <div className="team-standup-header">
              <h3><Users size={14} /> Today's Standups</h3>
              <button className="btn btn-secondary" onClick={handleRemind} disabled={reminding}>
                <Bell size={13} /> {reminded ? 'Sent!' : reminding ? 'Sending...' : 'Send Reminders'}
              </button>
            </div>
            {teamLoading && <div className="standup-loading">Loading team standups...</div>}
            {!teamLoading && teamEntries.length === 0 && (
              <div className="standup-empty-state">
                <Users size={24} />
                <p>No standups submitted yet today</p>
                <span>Send a reminder to nudge the team</span>
              </div>
            )}
            {teamEntries.map((entry) => (
              <TeamEntryCard key={entry.id} entry={entry} />
            ))}
          </div>
        )}

        {/* ── Meetings ── */}
        {tab === 'meetings' && (
          <div className="meetings-section fade-in" style={{ maxWidth: 720 }}>
            <div className="meetings-header">
              <h3><Calendar size={14} /> Standup Meetings</h3>
              <button className="btn btn-primary" onClick={() => openMeetingForm()}>
                <Plus size={13} /> New Meeting
              </button>
            </div>

            {/* Meeting Form Modal */}
            {showMeetingForm && (
              <div className="meeting-form-card">
                <div className="meeting-form-title">
                  {editingMeeting ? 'Edit Meeting' : 'New Standup Meeting'}
                </div>
                <div className="meeting-form-fields">
                  <div className="meeting-field">
                    <label>Title</label>
                    <input
                      value={meetingForm.title}
                      onChange={(e) => setMeetingForm({ ...meetingForm, title: e.target.value })}
                      placeholder="e.g. Daily Standup, Sprint Review"
                    />
                  </div>
                  <div className="meeting-field-row">
                    <div className="meeting-field">
                      <label>Time</label>
                      <input
                        type="time"
                        value={meetingForm.scheduled_time}
                        onChange={(e) => setMeetingForm({ ...meetingForm, scheduled_time: e.target.value })}
                      />
                    </div>
                    <div className="meeting-field">
                      <label>Frequency</label>
                      <select
                        value={meetingForm.frequency}
                        onChange={(e) => setMeetingForm({ ...meetingForm, frequency: e.target.value })}
                      >
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly (Mon)</option>
                        <option value="biweekly">Bi-weekly</option>
                        <option value="custom">Custom</option>
                      </select>
                    </div>
                  </div>
                  <div className="meeting-field">
                    <label>Participants</label>
                    <div className="meeting-participants">
                      {teamMembers.map((m) => (
                        <label key={m.id} className={`participant-chip ${meetingForm.participants.includes(m.id) ? 'selected' : ''}`}>
                          <input
                            type="checkbox"
                            checked={meetingForm.participants.includes(m.id)}
                            onChange={() => toggleParticipant(m.id)}
                          />
                          {m.name}
                        </label>
                      ))}
                      {teamMembers.length === 0 && <span className="meeting-no-members">No team members found</span>}
                    </div>
                  </div>
                  <div className="meeting-field">
                    <label>Notes (optional)</label>
                    <textarea
                      value={meetingForm.notes}
                      onChange={(e) => setMeetingForm({ ...meetingForm, notes: e.target.value })}
                      placeholder="Agenda, discussion topics..."
                      rows={2}
                    />
                  </div>
                </div>
                <div className="meeting-form-actions">
                  <button className="btn btn-primary" onClick={handleSaveMeeting} disabled={!meetingForm.title.trim()}>
                    <Save size={13} /> {editingMeeting ? 'Update' : 'Create'}
                  </button>
                  <button className="btn btn-secondary" onClick={() => setShowMeetingForm(false)}>Cancel</button>
                </div>
              </div>
            )}

            {meetingsLoading && <div className="standup-loading">Loading meetings...</div>}
            {!meetingsLoading && meetings.length === 0 && !showMeetingForm && (
              <div className="standup-empty-state">
                <Calendar size={24} />
                <p>No standup meetings scheduled</p>
                <span>Create a recurring standup to keep the team aligned</span>
              </div>
            )}
            {meetings.map((m) => (
              <div key={m.id} className="meeting-card">
                <div className="meeting-card-header">
                  <div className="meeting-card-info">
                    <span className="meeting-card-title">{m.title}</span>
                    <span className="meeting-card-schedule">
                      <Clock size={12} /> {m.scheduled_time} &middot; {m.frequency}
                    </span>
                  </div>
                  <div className="meeting-card-actions">
                    <button className="btn btn-ghost" onClick={() => openMeetingForm(m)} title="Edit">
                      <Edit3 size={13} />
                    </button>
                    <button className="btn btn-ghost" onClick={() => handleDeleteMeeting(m.id)} title="Delete" style={{ color: 'var(--p0-color)' }}>
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
                {(m.participants?.length > 0 || m.notes) && (
                  <div className="meeting-card-body">
                    {m.participants?.length > 0 && (
                      <div className="meeting-card-participants">
                        <Users size={12} />
                        {m.participants.map((p, i) => (
                          <span key={i} className="meeting-participant-tag">{p}</span>
                        ))}
                      </div>
                    )}
                    {m.notes && <p className="meeting-card-notes">{m.notes}</p>}
                  </div>
                )}
                <div className="meeting-card-footer">
                  <span>Created by {m.created_by}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── AI Standup ── */}
        {tab === 'ai' && (
          <div className="ai-standup-section fade-in">
            <div className="ai-standup-header">
              <h3><Sparkles size={14} /> AI-Generated Standup</h3>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-ghost" onClick={loadAi} disabled={aiLoading}>
                  <RefreshCw size={13} /> {aiLoading ? 'Generating...' : 'Regenerate'}
                </button>
                <button className="btn btn-primary" onClick={handleCopy} disabled={!aiStandup}>
                  {copied ? <><Check size={13} /> Copied!</> : <><Copy size={13} /> Copy</>}
                </button>
              </div>
            </div>
            {aiLoading && <div className="standup-loading">Generating AI standup...</div>}
            {aiStandup && !aiLoading && (
              <div className="ai-standup-content">
                {Object.entries(aiStandup.people || {}).map(([person, data]) => (
                  <div key={person} className="ai-person-card">
                    <h4>{person}</h4>
                    <div className="ai-section">
                      <span className="ai-section-label">Yesterday</span>
                      {data.yesterday.length > 0 ? (
                        <ul>{data.yesterday.map((item, i) => <li key={i}>{item}</li>)}</ul>
                      ) : <span className="ai-empty">(no activity)</span>}
                    </div>
                    <div className="ai-section">
                      <span className="ai-section-label">Today</span>
                      {data.today.length > 0 ? (
                        <ul>{data.today.map((item, i) => <li key={i}>{item}</li>)}</ul>
                      ) : <span className="ai-empty">(no tasks in progress)</span>}
                    </div>
                    {data.blockers.length > 0 && (
                      <div className="ai-section ai-blockers">
                        <span className="ai-section-label">Blockers</span>
                        <ul>{data.blockers.map((item, i) => <li key={i}>{item}</li>)}</ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Overview ── */}
        {tab === 'overview' && loading && <div className="standup-loading">Loading standup...</div>}

        {tab === 'overview' && standup && !loading && (
          <div className="standup-report fade-in">
            <div className="standup-date">{standup.date}</div>

            <StandupSection icon={<CheckCircle size={14} />} title="Completed" color="var(--status-done)" tasks={standup.completed} empty="No tasks completed yet" />
            <StandupSection icon={<Clock size={14} />} title="In Progress" color="var(--status-progress)" tasks={standup.in_progress} empty="Nothing in progress" />
            <StandupSection icon={<Eye size={14} />} title="Awaiting Review" color="var(--status-review)" tasks={standup.review} empty="No tasks in review" />
            <StandupSection icon={<AlertOctagon size={14} />} title="Blocked" color="var(--status-blocked)" tasks={standup.blocked} empty="Nothing blocked" />

            {standup.high_priority_backlog?.length > 0 && (
              <StandupSection icon={<AlertTriangle size={14} />} title="High Priority Backlog" color="var(--p0-color)" tasks={standup.high_priority_backlog} />
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

/* ── Sub-components ── */

function ChecklistSection({ title, icon, items, onToggle, onRemove, newValue, onNewChange, onAdd, placeholder, emptyText, variant }) {
  return (
    <div className={`checklist-group ${variant === 'blockers' ? 'checklist-blockers' : ''}`}>
      <div className="checklist-group-title">{icon} {title}</div>
      {items.length === 0 && <div className="checklist-empty">{emptyText}</div>}
      {items.map((item, i) => (
        <div key={i} className={`checklist-item ${item.checked ? '' : 'unchecked'}`}>
          <label className="checklist-checkbox">
            <input type="checkbox" checked={item.checked} onChange={() => onToggle(i)} />
          </label>
          <span className="checklist-text">{item.text}</span>
          <button className="btn btn-ghost checklist-remove" onClick={() => onRemove(i)}>
            <X size={11} />
          </button>
        </div>
      ))}
      <div className="checklist-add-row">
        <input
          value={newValue}
          onChange={(e) => onNewChange(e.target.value)}
          placeholder={placeholder}
          onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); onAdd(); } }}
        />
        <button className="btn btn-ghost" onClick={onAdd} disabled={!newValue.trim()}>
          <Plus size={13} />
        </button>
      </div>
    </div>
  );
}

function TeamEntryCard({ entry }) {
  const [expanded, setExpanded] = useState(true);
  return (
    <div className="team-entry-card">
      <div className="team-entry-header" onClick={() => setExpanded(!expanded)}>
        <div className="team-entry-avatar">{entry.username?.slice(0, 2).toUpperCase()}</div>
        <span className="team-entry-name">{entry.username}</span>
        <span className="team-entry-time">{new Date(entry.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </div>
      {expanded && (
        <div className="team-entry-body">
          {entry.yesterday?.length > 0 && (
            <div className="team-entry-section">
              <span className="team-entry-label">Yesterday</span>
              <ul>{entry.yesterday.map((item, i) => <li key={i}>{item}</li>)}</ul>
            </div>
          )}
          {entry.today?.length > 0 && (
            <div className="team-entry-section">
              <span className="team-entry-label">Today</span>
              <ul>{entry.today.map((item, i) => <li key={i}>{item}</li>)}</ul>
            </div>
          )}
          {entry.blockers?.length > 0 && (
            <div className="team-entry-section team-entry-blockers">
              <span className="team-entry-label">Blockers</span>
              <ul>{entry.blockers.map((item, i) => <li key={i}>{item}</li>)}</ul>
            </div>
          )}
          {entry.notes && (
            <div className="team-entry-section">
              <span className="team-entry-label">Notes</span>
              <p className="team-entry-notes">{entry.notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
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
