import { useDraggable } from '@dnd-kit/core';
import './TaskCard.css';

const AI_AGENTS = ['antigravity', 'claude-code'];

const TYPE_COLORS = {
  feature: '#773b93',
  bug: '#cc293d',
  'tech-debt': '#ca5010',
  research: '#0078d4',
  ops: '#8a8886',
};

function getInitials(name) {
  if (!name) return '?';
  return name.slice(0, 2).toUpperCase();
}

export default function TaskCard({ task, onClick, bulkMode, selected, onSelect }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: task.id,
    data: { task, status: task.status },
  });

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)`, zIndex: 999 }
    : {};

  const isAI = AI_AGENTS.includes(task.assignee);
  const isBlocked = task.status === 'blocked';
  const typeColor = TYPE_COLORS[task.type] || '#0078d4';
  const labels = Array.isArray(task.labels) ? task.labels : [];

  return (
    <div
      ref={setNodeRef}
      style={{ ...style, opacity: isDragging ? 0.3 : 1 }}
      className={`card ${isBlocked ? 'card-blocked' : ''} ${isDragging ? 'card-dragging' : ''}`}
      {...listeners}
      {...attributes}
    >
      {/* Bulk checkbox */}
      {bulkMode && (
        <label className="card-checkbox" onClick={(e) => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={selected}
            onChange={() => onSelect?.(task.id)}
          />
        </label>
      )}

      {/* Colored left bar */}
      <div
        className="card-drag-handle"
        style={{ background: typeColor }}
      />

      {/* Clickable card body */}
      <div className="card-body" onClick={() => onClick?.(task)}>
        <div className="card-title-row">
          <div className="card-type-icon" style={{ background: typeColor }}>
            <svg width="10" height="10" viewBox="0 0 16 16" fill="white">
              <rect x="2" y="2" width="12" height="12" rx="2" />
            </svg>
          </div>
          <span className="card-title">{task.title}</span>
        </div>

        <div className="card-assignee-row">
          <div className={`avatar ${isAI ? 'avatar-ai' : task.assignee ? 'avatar-human' : 'avatar-unassigned'}`}>
            {isAI ? 'AI' : task.assignee ? getInitials(task.assignee) : '?'}
          </div>
          <span className="card-assignee-name">{task.assignee || 'Unassigned'}</span>
        </div>

        {labels.length > 0 && (
          <div className="card-labels">
            {labels.map((label) => (
              <span key={label} className="label-chip">{label}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
