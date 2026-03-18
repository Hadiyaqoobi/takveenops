import { useState, useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import { getAnalyticsSummary, getVelocity, getCycleTime, getAiRatio, getWorkload,
         getAiVelocity, getAiCostPerPoint, getAgentPerformance } from '../api';
import './AnalyticsPage.css';

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [velocity, setVelocity] = useState([]);
  const [cycleTime, setCycleTime] = useState([]);
  const [aiRatio, setAiRatio] = useState([]);
  const [workload, setWorkload] = useState(null);
  const [aiVelocity, setAiVelocity] = useState([]);
  const [aiCostPerPoint, setAiCostPerPoint] = useState([]);
  const [agentPerf, setAgentPerf] = useState([]);

  useEffect(() => {
    getAnalyticsSummary().then(setSummary).catch(console.error);
    getVelocity().then(setVelocity).catch(console.error);
    getCycleTime().then(setCycleTime).catch(console.error);
    getAiRatio().then(setAiRatio).catch(console.error);
    getWorkload().then(setWorkload).catch(console.error);
    getAiVelocity().then(setAiVelocity).catch(console.error);
    getAiCostPerPoint().then(setAiCostPerPoint).catch(console.error);
    getAgentPerformance().then(setAgentPerf).catch(console.error);
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

            {/* Workload Heatmap */}
            {workload?.workload && Object.keys(workload.workload).length > 0 && (
              <div className="analytics-card" style={{ gridColumn: '1 / -1' }}>
                <h3>Workload Heatmap</h3>
                <div className="heatmap">
                  <div className="heatmap-row heatmap-header-row">
                    <div className="heatmap-label"></div>
                    {['backlog', 'in-progress', 'review', 'done', 'blocked'].map((s) => (
                      <div key={s} className="heatmap-col-header">{s}</div>
                    ))}
                  </div>
                  {Object.entries(workload.workload).map(([member, statuses]) => (
                    <div key={member} className="heatmap-row">
                      <div className="heatmap-label">{member}</div>
                      {['backlog', 'in-progress', 'review', 'done', 'blocked'].map((s) => {
                        const count = statuses[s] || 0;
                        const intensity = Math.min(1, count / 5);
                        return (
                          <div
                            key={s}
                            className="heatmap-cell"
                            style={{ background: `rgba(0, 120, 212, ${0.1 + intensity * 0.7})` }}
                            title={`${member}: ${count} ${s}`}
                          >
                            {count || ''}
                          </div>
                        );
                      })}
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

            {/* AI vs Human Velocity by Sprint */}
            {aiVelocity.length > 0 && (
              <div className="analytics-card">
                <h3>AI vs Human Velocity by Sprint</h3>
                <div className="bar-chart">
                  {aiVelocity.map((r, i) => (
                    <div key={i} className="bar-row">
                      <span className="bar-label">Sprint {r.sprint_id} — {r.worker_type}</span>
                      <div className="bar-track">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${Math.min(100, r.tasks_done * 10)}%`,
                            background: r.worker_type === 'ai' ? 'var(--accent)' : 'var(--status-done)',
                          }}
                        />
                      </div>
                      <span className="bar-value">{r.tasks_done} tasks ({r.story_points}h)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Cost per Story Point */}
            {aiCostPerPoint.length > 0 && (
              <div className="analytics-card">
                <h3>AI Cost per Story Point</h3>
                <div className="bar-chart">
                  {aiCostPerPoint.map((r) => (
                    <div key={r.agent_id} className="bar-row">
                      <span className="bar-label">{r.agent_id}</span>
                      <span className="bar-value">
                        ${r.total_cost?.toFixed(4) || '0.0000'} total
                        &nbsp;&middot;&nbsp;${r.cost_per_point?.toFixed(4) || '0.0000'}/pt
                        &nbsp;&middot;&nbsp;{r.tasks_touched} tasks
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Agent Performance Comparison */}
            {agentPerf.length > 0 && (
              <div className="analytics-card" style={{ gridColumn: '1 / -1' }}>
                <h3>Agent Performance Comparison</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      {['Agent', 'Model', 'Sessions', 'Tasks Done', 'Total Tokens', 'Total Cost', 'Avg Duration', 'Success Rate'].map(h => (
                        <th key={h} style={{ textAlign: 'left', padding: '4px 8px', color: 'var(--text-muted)' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {agentPerf.map((r) => (
                      <tr key={`${r.agent_id}-${r.model}`} style={{ borderBottom: '1px solid var(--border-light, var(--border))' }}>
                        <td style={{ padding: '4px 8px', fontWeight: 500 }}>{r.agent_id}</td>
                        <td style={{ padding: '4px 8px', color: 'var(--text-secondary)' }}>{r.model}</td>
                        <td style={{ padding: '4px 8px' }}>{r.total_sessions}</td>
                        <td style={{ padding: '4px 8px' }}>{r.tasks_done}</td>
                        <td style={{ padding: '4px 8px' }}>{r.total_tokens?.toLocaleString() || 0}</td>
                        <td style={{ padding: '4px 8px' }}>${r.total_cost?.toFixed(4) || '0.0000'}</td>
                        <td style={{ padding: '4px 8px' }}>{r.avg_duration ? `${r.avg_duration.toFixed(0)}s` : '—'}</td>
                        <td style={{ padding: '4px 8px' }}>
                          {r.total_sessions > 0
                            ? `${Math.round((r.completed_sessions / r.total_sessions) * 100)}%`
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {!summary && <div className="standup-loading">Loading analytics...</div>}
      </div>
    </>
  );
}
