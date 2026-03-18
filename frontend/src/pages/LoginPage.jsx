import { useState, useEffect } from 'react';
import { Zap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { wakeServer, validateInvite, acceptInvite } from '../api';
import './LoginPage.css';

export default function LoginPage() {
  const { login, register, setUser } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', display_name: '', email: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [serverReady, setServerReady] = useState(false);

  // Invite flow
  const [inviteToken, setInviteToken] = useState(null);
  const [inviteInfo, setInviteInfo] = useState(null);
  const [inviteLoading, setInviteLoading] = useState(false);

  // Wake up the Render server as soon as the login page loads
  useEffect(() => {
    wakeServer().then(() => setServerReady(true));
  }, []);

  // Check for invite token in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('invite');
    if (token) {
      setInviteToken(token);
      setIsRegister(true);
      setInviteLoading(true);
      validateInvite(token)
        .then((info) => {
          setInviteInfo(info);
          setForm((f) => ({ ...f, email: info.email }));
        })
        .catch((err) => {
          setError(err.message || 'Invalid or expired invitation');
          setInviteToken(null);
        })
        .finally(() => setInviteLoading(false));
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (inviteToken) {
        // Accept invitation flow
        const res = await acceptInvite({
          token: inviteToken,
          username: form.username,
          password: form.password,
          display_name: form.display_name,
        });
        // Store token and set user
        localStorage.setItem('takvenops_token', res.token);
        localStorage.setItem('takvenops_refresh_token', res.refresh_token);
        if (setUser) setUser(res.user);
        // Clean URL
        window.history.replaceState({}, '', '/');
        window.location.reload();
      } else if (isRegister) {
        await register(form.username, form.password, form.display_name, form.email);
      } else {
        await login(form.username, form.password);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed');
    }
    setLoading(false);
  };

  return (
    <div className="login-page">
      <div className="login-header">
        <Zap size={20} />
        <span>TakvenOps</span>
      </div>

      <div className="login-card">
        <h2>{inviteToken ? 'Accept Invitation' : isRegister ? 'Create Account' : 'Sign In'}</h2>
        <p className="login-subtitle">
          {inviteToken
            ? `You've been invited to join ${inviteInfo?.project_id === 'default' ? 'TakvenOps' : inviteInfo?.project_id || 'TakvenOps'}`
            : isRegister ? 'Join your team on TakvenOps' : 'Welcome back to TakvenOps'}
        </p>

        {inviteToken && inviteInfo && (
          <div style={{ background: 'var(--bg-page)', padding: '8px 12px', borderRadius: 4, marginBottom: 12, fontSize: 13 }}>
            Invitation for <strong>{inviteInfo.email}</strong> as <strong>{inviteInfo.role}</strong>
          </div>
        )}

        {inviteLoading && (
          <div className="login-waking">Validating invitation...</div>
        )}

        {!serverReady && (
          <div className="login-waking">
            Waking up server... This may take up to 60 seconds on first visit.
          </div>
        )}

        {error && <div className="login-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              autoFocus
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              placeholder="Choose a username"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="Enter password"
              required
            />
          </div>

          {(isRegister || inviteToken) && (
            <div className="form-group">
              <label>Display Name</label>
              <input
                value={form.display_name}
                onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                placeholder="How your name appears"
              />
            </div>
          )}

          {isRegister && !inviteToken && (
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="your@email.com"
              />
            </div>
          )}

          <button type="submit" className="btn btn-primary login-btn" disabled={loading || inviteLoading}>
            {loading ? 'Connecting to server...' : inviteToken ? 'Accept & Join' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        {!inviteToken && (
          <div className="login-toggle">
            {isRegister ? (
              <span>Already have an account? <button onClick={() => setIsRegister(false)}>Sign In</button></span>
            ) : (
              <span>Don't have an account? <button onClick={() => setIsRegister(true)}>Create one</button></span>
            )}
          </div>
        )}

        {!inviteToken && (
          <div className="login-hint">
            Default login: <strong>admin</strong> / <strong>admin123</strong>
          </div>
        )}
      </div>
    </div>
  );
}
