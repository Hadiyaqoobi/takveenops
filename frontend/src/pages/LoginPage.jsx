import { useState, useEffect } from 'react';
import { Zap } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { wakeServer } from '../api';
import './LoginPage.css';

export default function LoginPage() {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ username: '', password: '', display_name: '', email: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [serverReady, setServerReady] = useState(false);

  // Wake up the Render server as soon as the login page loads
  useEffect(() => {
    wakeServer().then(() => setServerReady(true));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
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
        <h2>{isRegister ? 'Create Account' : 'Sign In'}</h2>
        <p className="login-subtitle">
          {isRegister ? 'Join your team on TakvenOps' : 'Welcome back to TakvenOps'}
        </p>

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
              placeholder="Enter username"
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

          {isRegister && (
            <>
              <div className="form-group">
                <label>Display Name</label>
                <input
                  value={form.display_name}
                  onChange={(e) => setForm({ ...form, display_name: e.target.value })}
                  placeholder="How your name appears"
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="your@email.com"
                />
              </div>
            </>
          )}

          <button type="submit" className="btn btn-primary login-btn" disabled={loading}>
            {loading ? 'Connecting to server...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="login-toggle">
          {isRegister ? (
            <span>Already have an account? <button onClick={() => setIsRegister(false)}>Sign In</button></span>
          ) : (
            <span>Don't have an account? <button onClick={() => setIsRegister(true)}>Create one</button></span>
          )}
        </div>

        <div className="login-hint">
          Default login: <strong>admin</strong> / <strong>admin123</strong>
        </div>
      </div>
    </div>
  );
}
