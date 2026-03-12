import { useState, useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import { getAnalyticsSummary, getVelocity, getCycleTime, getAiRatio } from '../api';
import './AnalyticsPage.css';

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [velocity, setVelocity] = useState([]);
  const [cycleTime, setCycleTime] = useState([]);
  const [aiRatio, setAiRatio] = useState([]);

  useEffect(() => {
    getAnalyticsSummary().then(setSummary).catch(console.error);
    getVelocity().then(setVelocity).catch(console.error);
    getCycleTime().then(setCycleTime).catch(console.error);
    getAiRatio().then(setAiRatio).catch(console.error);
  }, []);

  const statusColors = {
    backlog: 'var(--status-backlog)',
    'in-progress': 'var(--status-progress)',
    review: 'var(--status-review)',
    done: 'var(--status-done)',
    blocked: 'var(--status-blocked)',
  };

  const priorityColors = {
    P0: 'var(--p0-color)',
    P1: 'var(--p1-color)',
    P2: 'var(--p2-color)',
    P3: 'var(--p3-color)',
  };

  return (
    <>
      <div className="page-header">
        <h1><BarChart3 size={16} /> Analytics</h1>
      </div>

      <div className="page-body">
        {summary && (
          <div className="analytics-grid fade-in">
            {/* Total tasks */}
            <div className="stat-card">
              <div className="stat-value">{summary.total_tasks}</div>
              <div className="stat-label">Total Tasks</div>
            </div>

            {/* By Status */}
            <div className="analytics-card">
              <h3>By Status</h3>
              <div className="bar-chart">
                {Object.entries(summary.by_status).map(([status, count]) => (
                  <div key={status} className="bar-row">
                    <span className="bar-label">{status}</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${(count / summary.total_tasks) * 100}%`,
                          background: statusColors[status] || 'var(--accent)',
                        }}
                      />
                    </div>
                    <span className="bar-value">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* By Priority */}
            <div className="analytics-card">
              <h3>By Priority</h3>
              <div className="bar-chart">
                {Object.entries(summary.by_priority).map(([p, count]) => (
                  <div key={p} className="bar-row">
                    <span className="bar-label">{p}</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width: `${(count / summary.total_tasks) * 100}%`,
                          background: priorityColors[p] || 'var(--accent)',
                        }}
                      />
                    </div>
                    <span className="bar-value">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* By Type */}
            <div className="analytics-card">
              <h3>By Type</h3>
              <div className="bar-chart">
                {Object.entries(summary.by_type).map(([t, count]) => (
                  <div key={t} className="bar-row">
                    <span className="bar-label">{t}</span>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${(count / summary.total_tasks) * 100}%` }} />
                    </div>
                    <span className="bar-value">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* By Assignee */}
            {Object.keys(summary.by_assignee).length > 0 && (
              <div className="analytics-card">
                <h3>By Assignee</h3>
                <div className="bar-chart">
                  {Object.entries(summary.by_assignee).map(([a, count]) => (
                    <div key={a} className="bar-row">
                      <span className="bar-label">{a}</span>
                      <div className="bar-track">
                        <div className="bar-fill" style={{ width: `${(count / summary.total_tasks) * 100}%` }} />
                      </div>
                      <span className="bar-value">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI vs Human */}
            {aiRatio.length > 0 && (
              <div className="analytics-card">
                <h3>AI vs Human (Done)</h3>
                <div className="ratio-chips">
                  {aiRatio.map((r) => (
                    <div key={r.worker_type} className="ratio-chip">
                      <span className="ratio-type">{r.worker_type}</span>
                      <span className="ratio-count">{r.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Cycle Time */}
            {cycleTime.length > 0 && (
              <div className="analytics-card">
                <h3>Avg Cycle Time (days)</h3>
                <div className="bar-chart">
                  {cycleTime.map((c) => (
                    <div key={c.assignee || 'none'} className="bar-row">
                      <span className="bar-label">{c.assignee || 'Unassigned'}</span>
                      <span className="bar-value">{c.avg_days?.toFixed(1) || '—'} days ({c.count} tasks)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {!summary && <div className="standup-loading">Loading analytics...</div>}
      </div>
    </>
  );
}
