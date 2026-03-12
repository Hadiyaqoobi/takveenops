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

// Analytics
export const getVelocity = () => request('/analytics/velocity');
export const getBurndown = () => request('/analytics/burndown');
export const getAiRatio = () => request('/analytics/ai-ratio');
export const getCycleTime = () => request('/analytics/cycle-time');
export const getAnalyticsSummary = () => request('/analytics/summary');

// Health
export const healthCheck = () => request('/health');
