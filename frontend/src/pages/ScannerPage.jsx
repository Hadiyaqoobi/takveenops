import { useState, useEffect } from 'react';
import { ScanSearch, Play, FileCode, AlertTriangle, TestTube, Plus } from 'lucide-react';
import { runScan, getScanResults, createTask } from '../api';
import './ScannerPage.css';

const TYPE_ICONS = {
  todo: <FileCode size={14} />,
  missing_test: <TestTube size={14} />,
  error_handling: <AlertTriangle size={14} />,
};

const TYPE_LABELS = {
  todo: 'TODO/FIXME Comments',
  missing_test: 'Missing Tests',
  error_handling: 'Missing Error Handling',
};

export default function ScannerPage() {
  const [repoPath, setRepoPath] = useState('');
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    getScanResults().then(setHistory).catch(console.error);
  }, []);

  const handleScan = async () => {
    if (!repoPath.trim()) return;
    setScanning(true);
    try {
      const res = await runScan(repoPath);
      setResults(res);
      getScanResults().then(setHistory).catch(console.error);
    } catch (e) {
      console.error(e);
    }
    setScanning(false);
  };

  const handleCreateTask = async (issue) => {
    try {
      await createTask({
        title: `[${issue.tag}] ${issue.text.slice(0, 60)}`,
        type: issue.type === 'todo' ? 'tech-debt' : 'bug',
        priority: issue.severity || 'P2',
        labels: [issue.type],
        files_involved: [issue.file],
        body_markdown: `Found by scanner:\n\`${issue.file}:${issue.line}\`\n\n${issue.text}`,
      });
      alert('Task created!');
    } catch (e) {
      console.error(e);
    }
  };

  const grouped = {};
  if (results?.issues) {
    results.issues.forEach((issue) => {
      if (!grouped[issue.type]) grouped[issue.type] = [];
      grouped[issue.type].push(issue);
    });
  }

  return (
    <>
      <div className="page-header">
        <h1><ScanSearch size={16} /> Codebase Scanner</h1>
      </div>

      <div className="page-body">
        <div className="scanner-controls">
          <input
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="Enter repo path (e.g., C:\Users\hyaqo\Desktop\myproject)"
            className="scanner-input"
          />
          <button className="btn btn-primary" onClick={handleScan} disabled={scanning}>
            <Play size={14} /> {scanning ? 'Scanning...' : 'Run Scan'}
          </button>
        </div>

        {results && (
          <div className="scanner-results fade-in">
            <div className="scanner-summary">
              Found <strong>{results.total}</strong> issues
            </div>

            {Object.entries(grouped).map(([type, issues]) => (
              <div key={type} className="scanner-group">
                <h3>
                  {TYPE_ICONS[type]} {TYPE_LABELS[type] || type}
                  <span className="section-count">{issues.length}</span>
                </h3>
                <div className="scanner-issues">
                  {issues.slice(0, 20).map((issue, i) => (
                    <div key={i} className="scanner-issue">
                      <div className="issue-file">{issue.file}:{issue.line}</div>
                      <div className="issue-text">{issue.text}</div>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleCreateTask(issue)}>
                        <Plus size={12} /> Task
                      </button>
                    </div>
                  ))}
                  {issues.length > 20 && (
                    <div className="scanner-more">...and {issues.length - 20} more</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {history.length > 0 && (
          <div className="scanner-history">
            <h3>Scan History</h3>
            {history.map((h) => (
              <div key={h.id} className="history-row">
                <span>{h.scan_date}</span>
                <span>{h.total_issues} issues</span>
                <span className="history-path">{h.repo_path}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
