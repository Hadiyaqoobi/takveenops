/** TakvenOps API client */

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8001') + '/api';

function getAuthHeaders() {
  const token = localStorage.getItem('takvenops_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Wake up the server — call this early so it starts booting
let _wakePromise = null;
export function wakeServer() {
  if (_wakePromise) return _wakePromise;
  _wakePromise = fetch(`${API_BASE}/health`, { method: 'GET' })
    .catch(() => {})
    .finally(() => { setTimeout(() => { _wakePromise = null; }, 30000); });
  return _wakePromise;
}

async function singleRequest(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders(), ...options.headers },
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  } catch (e) {
    clearTimeout(timeout);
    throw e;
  }
}

async function request(path, options = {}) {
  const maxRetries = 3;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await singleRequest(path, options);
    } catch (e) {
      const isNetworkError = e.name === 'AbortError' || e.message === 'Failed to fetch';
      if (isNetworkError && attempt < maxRetries) {
        // Wait before retry — server is likely cold-starting
        await new Promise((r) => setTimeout(r, attempt * 5000));
        continue;
      }
      if (e.name === 'AbortError') {
        throw new Error('Server is still starting up. Please wait a moment and try again.');
      }
      if (e.message === 'Failed to fetch') {
        throw new Error('Cannot reach server — it may be starting up. Please wait a moment and try again.');
      }
      throw e;
    }
  }
}

// Auth
export const loginUser = (username, password) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });

export const registerUser = (username, password, display_name, email) =>
  request('/auth/register', { method: 'POST', body: JSON.stringify({ username, password, display_name, email }) });

export const getCurrentUser = (token) =>
  fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
    .then((r) => { if (!r.ok) throw new Error('Not authenticated'); return r.json(); });

export const logoutUser = (token) =>
  fetch(`${API_BASE}/auth/logout`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });

// Profile
export const getProfileDashboard = () => request('/profile/dashboard');
export const updateProfile = (data) => request('/profile/update', { method: 'PUT', body: JSON.stringify(data) });

// Tasks
export const getTasks = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/tasks${qs ? '?' + qs : ''}`);
};
export const getTask = (id) => request(`/tasks/${id}`);
export const createTask = (data) => request('/tasks', { method: 'POST', body: JSON.stringify(data) });
export const updateTask = (id, data) => request(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteTask = (id) => request(`/tasks/${id}`, { method: 'DELETE' });
export const moveTask = (id, status) => request(`/tasks/${id}/move`, { method: 'POST', body: JSON.stringify({ status }) });
export const assignTask = (id, assignee) => request(`/tasks/${id}/assign`, { method: 'POST', body: JSON.stringify({ assignee }) });

// Sprints
export const getSprints = () => request('/sprints');
export const createSprint = (data) => request('/sprints', { method: 'POST', body: JSON.stringify(data) });
export const updateSprint = (id, data) => request(`/sprints/${id}`, { method: 'PUT', body: JSON.stringify(data) });

// Team
export const getTeam = () => request('/team');
export const addTeamMember = (data) => request('/team', { method: 'POST', body: JSON.stringify(data) });
export const updateTeamMember = (id, data) => request(`/team/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteTeamMember = (id) => request(`/team/${id}`, { method: 'DELETE' });

// Scanner
export const runScan = (repoPath) => request('/scanner/run', { method: 'POST', body: JSON.stringify({ repo_path: repoPath }) });
export const getScanResults = () => request('/scanner/results');

// Standup
export const getStandup = () => request('/standup/today');
export const getStandupHistory = () => request('/standup/history');
export const getMyChecklist = () => request('/standup/my-checklist');
export const submitStandup = (data) => request('/standup/submit', { method: 'POST', body: JSON.stringify(data) });
export const getStandupEntries = (standupDate) => request(`/standup/entries${standupDate ? '?standup_date=' + standupDate : ''}`);
export const getMyStandupEntries = () => request('/standup/entries/mine');
export const sendStandupReminders = () => request('/standup/send-reminders', { method: 'POST' });
export const getStandupMeetings = () => request('/standup/meetings');
export const createStandupMeeting = (data) => request('/standup/meetings', { method: 'POST', body: JSON.stringify(data) });
export const updateStandupMeeting = (id, data) => request(`/standup/meetings/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteStandupMeeting = (id) => request(`/standup/meetings/${id}`, { method: 'DELETE' });

// Analytics
export const getVelocity = () => request('/analytics/velocity');
export const getBurndown = () => request('/analytics/burndown');
export const getAiRatio = () => request('/analytics/ai-ratio');
export const getCycleTime = () => request('/analytics/cycle-time');
export const getAnalyticsSummary = () => request('/analytics/summary');

// Comments & Activity
export const getComments = (taskId) => request(`/tasks/${taskId}/comments`);
export const addComment = (taskId, body) => request(`/tasks/${taskId}/comments`, { method: 'POST', body: JSON.stringify({ body }) });
export const getTaskActivity = (taskId) => request(`/tasks/${taskId}/activity`);

// Notifications
export const getNotifications = (unread) => request(`/notifications${unread ? '?unread=true' : ''}`);
export const getUnreadCount = () => request('/notifications/unread-count');
export const markNotificationRead = (id) => request(`/notifications/${id}/read`, { method: 'PATCH' });
export const markAllNotificationsRead = () => request('/notifications/read-all', { method: 'POST' });

// Natural Language Parse
export const parseTaskText = (text) => request('/tasks/parse', { method: 'POST', body: JSON.stringify({ text }) });

// GitHub
export const getGitHubConfig = () => request('/github/config');
export const setupGitHub = (data) => request('/github/setup', { method: 'POST', body: JSON.stringify(data) });
export const disconnectGitHub = () => request('/github/disconnect', { method: 'DELETE' });
export const getTaskLinks = (taskId) => request(`/github/tasks/${taskId}/links`);

// AI Standup
export const getAiStandup = () => request('/standup/ai-generate');

// Subtasks & Dependencies
export const getSubtasks = (taskId) => request(`/tasks/${taskId}/subtasks`);
export const getDependencies = (taskId) => request(`/tasks/${taskId}/dependencies`);

// Sprint Planning
export const getSprintSuggestions = (sprintId) => request(`/sprints/${sprintId}/suggestions`);
export const addTaskToSprint = (sprintId, taskId) => request(`/sprints/${sprintId}/add-task`, { method: 'POST', body: JSON.stringify({ task_id: taskId }) });
export const removeTaskFromSprint = (sprintId, taskId) => request(`/sprints/${sprintId}/remove-task`, { method: 'POST', body: JSON.stringify({ task_id: taskId }) });

// Templates
export const getTemplates = () => request('/templates');
export const createTemplate = (data) => request('/templates', { method: 'POST', body: JSON.stringify(data) });
export const deleteTemplate = (id) => request(`/templates/${id}`, { method: 'DELETE' });

// Time Tracking
export const getTimeEntries = (taskId) => request(`/tasks/${taskId}/time`);
export const logTime = (taskId, data) => request(`/tasks/${taskId}/time`, { method: 'POST', body: JSON.stringify(data) });
export const deleteTimeEntry = (taskId, entryId) => request(`/tasks/${taskId}/time/${entryId}`, { method: 'DELETE' });

// My Day
export const getMyDay = () => request('/my-day');

// Auto-Assign
export const autoAssignTasks = (taskIds) => request('/tasks/auto-assign', { method: 'POST', body: JSON.stringify({ task_ids: taskIds || [] }) });

// Escalation
export const checkEscalation = () => request('/tasks/check-escalation', { method: 'POST' });

// Recurring
export const getRecurringRules = () => request('/recurring');
export const createRecurringRule = (data) => request('/recurring', { method: 'POST', body: JSON.stringify(data) });
export const deleteRecurringRule = (id) => request(`/recurring/${id}`, { method: 'DELETE' });
export const runRecurringRules = () => request('/recurring/run', { method: 'POST' });

// Webhooks
export const getWebhooks = () => request('/webhooks');
export const createWebhook = (data) => request('/webhooks', { method: 'POST', body: JSON.stringify(data) });
export const deleteWebhook = (id) => request(`/webhooks/${id}`, { method: 'DELETE' });
export const testWebhook = (id) => request(`/webhooks/${id}/test`, { method: 'POST' });

// Bulk Operations
export const bulkAction = (action, taskIds, params = {}) =>
  request('/tasks/bulk', { method: 'POST', body: JSON.stringify({ action, task_ids: taskIds, params }) });

// Calendar
export const getCalendarTasks = (month) => request(`/tasks/calendar${month ? '?month=' + month : ''}`);

// Workload Heatmap
export const getWorkload = () => request('/analytics/workload');

// Sprint Report
export const getSprintReport = (sprintId) => request(`/sprints/${sprintId}/report`);
export const downloadSprintReportCSV = (sprintId) => {
  const url = `${(import.meta.env.VITE_API_URL || 'http://localhost:8001')}/api/sprints/${sprintId}/report?format=csv`;
  window.open(url, '_blank');
};

// File Uploads
export const UPLOADS_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8001');

async function uploadRequest(path, formData) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { ...getAuthHeaders() },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export const uploadTaskAttachment = (taskId, file) => {
  const fd = new FormData();
  fd.append('file', file);
  return uploadRequest(`/tasks/${taskId}/attachments`, fd);
};
export const getTaskAttachments = (taskId) => request(`/tasks/${taskId}/attachments`);
export const deleteTaskAttachment = (taskId, id) => request(`/tasks/${taskId}/attachments/${id}`, { method: 'DELETE' });

export const uploadAvatar = (file) => {
  const fd = new FormData();
  fd.append('file', file);
  return uploadRequest('/profile/avatar', fd);
};

// Projects
export const getProjects = () => request('/projects');
export const createProject = (data) => request('/projects', { method: 'POST', body: JSON.stringify(data) });
export const getProject = (id) => request(`/projects/${id}`);
export const updateProject = (id, data) => request(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const getProjectMembers = (id) => request(`/projects/${id}/members`);
export const addProjectMember = (id, data) => request(`/projects/${id}/members`, { method: 'POST', body: JSON.stringify(data) });

// AI Agent Sessions
export const startAgentSession = (data) => request('/ai/sessions/start', { method: 'POST', body: JSON.stringify(data) });
export const endAgentSession = (id, data) => request(`/ai/sessions/${id}/end`, { method: 'POST', body: JSON.stringify(data) });
export const getAgentSessions = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/ai/sessions${qs ? '?' + qs : ''}`);
};
export const getAiCostSummary = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/ai/cost-summary${qs ? '?' + qs : ''}`);
};

// AI-Enhanced Analytics
export const getAiVelocity = (projectId) => request(`/analytics/ai-velocity${projectId ? '?project_id=' + projectId : ''}`);
export const getAiCostPerPoint = (projectId) => request(`/analytics/ai-cost-per-point${projectId ? '?project_id=' + projectId : ''}`);
export const getAgentPerformance = (projectId) => request(`/analytics/agent-performance${projectId ? '?project_id=' + projectId : ''}`);

// Task Decomposition
export const decomposeEpic = (data) => request('/tasks/decompose', { method: 'POST', body: JSON.stringify(data) });

// Search
export const searchTasks = (q, projectId) => {
  const qs = new URLSearchParams({ q, ...(projectId ? { project_id: projectId } : {}) }).toString();
  return request(`/tasks/search?${qs}`);
};

// Auth Refresh
export const refreshAuthToken = (refreshToken) =>
  request('/auth/refresh', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) });

// Health
export const healthCheck = () => request('/health');

// Invitations
export const sendInvitation = (data) => request('/invitations', { method: 'POST', body: JSON.stringify(data) });
export const getInvitations = () => request('/invitations');
export const revokeInvitation = (id) => request(`/invitations/${id}`, { method: 'DELETE' });
export const resendInvitation = (id) => request(`/invitations/${id}/resend`, { method: 'POST' });
export const validateInvite = (token) => request(`/invitations/validate?token=${token}`);
export const acceptInvite = (data) => request('/invitations/accept', { method: 'POST', body: JSON.stringify(data) });

// Email Preferences
export const getEmailPreferences = () => request('/profile/email-preferences');
export const updateEmailPreferences = (data) => request('/profile/email-preferences', { method: 'PUT', body: JSON.stringify(data) });
