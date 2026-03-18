import { Keyboard, X } from 'lucide-react';
import './ShortcutsModal.css';

const SHORTCUTS = [
  { keys: ['C'], description: 'Create new task' },
  { keys: ['/'], description: 'Open command palette' },
  { keys: ['Ctrl', 'K'], description: 'Open command palette' },
  { keys: ['?'], description: 'Show keyboard shortcuts' },
  { keys: ['Esc'], description: 'Close panel / modal' },
];

export default function ShortcutsModal({ onClose }) {
  return (
    <div className="cmd-overlay" onClick={onClose}>
      <div className="shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="shortcuts-header">
          <h2><Keyboard size={16} /> Keyboard Shortcuts</h2>
          <button className="btn btn-ghost" onClick={onClose}><X size={16} /></button>
        </div>
        <div className="shortcuts-body">
          <table className="shortcuts-table">
            <tbody>
              {SHORTCUTS.map((s, i) => (
                <tr key={i}>
                  <td className="shortcut-keys">
                    {s.keys.map((k, j) => (
                      <span key={j}>
                        <kbd className="shortcut-kbd">{k}</kbd>
                        {j < s.keys.length - 1 && <span className="shortcut-plus">+</span>}
                      </span>
                    ))}
                  </td>
                  <td className="shortcut-desc">{s.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
