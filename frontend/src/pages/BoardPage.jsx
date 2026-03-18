import { useState, useEffect, useCallback } from 'react';
import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors, useDroppable, rectIntersection } from '@dnd-kit/core';
import { Plus, Filter, Wand2, CheckSquare } from 'lucide-react';
import TaskCard from '../components/TaskCard';
import TaskDetail from '../components/TaskDetail';
import CreateTaskModal from '../components/CreateTaskModal';
import QuickAddBar from '../components/QuickAddBar';
import BulkActionBar from '../components/BulkActionBar';
import { getTasks, moveTask, autoAssignTasks } from '../api';
import { useProject } from '../contexts/ProjectContext';
import useWebSocket from '../hooks/useWebSocket';
import './BoardPage.css';

const COLUMNS = [
  { id: 'backlog', label: 'New' },
  { id: 'in-progress', label: 'Active' },
  { id: 'review', label: 'Resolved' },
  { id: 'done', label: 'Closed' },
  { id: 'blocked', label: 'Blocked' },
];

const COLUMN_IDS = new Set(COLUMNS.map((c) => c.id));

const TYPE_COLORS = {
  feature: '#773b93',
  bug: '#cc293d',
  'tech-debt': '#ca5010',
  research: '#0078d4',
  ops: '#8a8886',
};

function DroppableColumn({ id, label, tasks, onTaskClick, bulkMode, selectedIds, onSelect }) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div ref={setNodeRef} className={`board-col ${isOver ? 'board-col-over' : ''}`}>
      <div className="board-col-header">
        <span className="board-col-title">{label}</span>
        <span className="board-col-count">{tasks.length}</span>
      </div>
      <div className="board-col-body">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onClick={onTaskClick}
            bulkMode={bulkMode}
            selected={selectedIds?.has(task.id)}
            onSelect={onSelect}
          />
        ))}
        {tasks.length === 0 && (
          <div className="board-col-empty">Drop items here</div>
        )}
      </div>
    </div>
  );
}

export default function BoardPage() {
  const { currentProject } = useProject();
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [filterAssignee, setFilterAssignee] = useState('');
  const [bulkMode, setBulkMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [autoAssigning, setAutoAssigning] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  const loadTasks = useCallback(async () => {
    try {
      setTasks(await getTasks({ project_id: currentProject }));
    } catch (e) {
      console.error('Failed to load tasks:', e);
    }
  }, [currentProject]);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  // WebSocket real-time updates
  useWebSocket(useCallback((msg) => {
    if (['task_created', 'task_moved', 'task_deleted', 'task_assigned'].includes(msg.event)) {
      loadTasks();
    }
  }, [loadTasks]));

  const handleAutoAssign = async () => {
    setAutoAssigning(true);
    try {
      await autoAssignTasks();
      loadTasks();
    } catch (e) {
      console.error('Auto-assign failed:', e);
    }
    setAutoAssigning(false);
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Filter
  let filtered = tasks;
  if (filterType) filtered = filtered.filter((t) => t.type === filterType);
  if (filterAssignee) filtered = filtered.filter((t) => t.assignee === filterAssignee);

  const tasksByStatus = {};
  COLUMNS.forEach((col) => {
    tasksByStatus[col.id] = filtered.filter((t) => t.status === col.id);
  });

  const uniqueAssignees = [...new Set(tasks.map((t) => t.assignee).filter(Boolean))];

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const taskId = active.id;
    let targetColumnId = over.id;

    // If dropped over a column droppable, over.id is the column id
    // If dropped over another card, over.id would be a task id — shouldn't happen
    // since cards use useDraggable (not droppable), but just in case:
    if (!COLUMN_IDS.has(targetColumnId)) {
      // Find which column this task belongs to
      const overTask = tasks.find((t) => t.id === targetColumnId);
      if (overTask) {
        targetColumnId = overTask.status;
      } else {
        return; // Unknown drop target
      }
    }

    const task = tasks.find((t) => t.id === taskId);
    if (!task || task.status === targetColumnId) return;

    // Optimistic update
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: targetColumnId } : t))
    );

    try {
      await moveTask(taskId, targetColumnId);
    } catch {
      loadTasks(); // Revert on error
    }
  };

  const activeTask = activeId ? tasks.find((t) => t.id === activeId) : null;
  const activeTypeColor = activeTask ? (TYPE_COLORS[activeTask.type] || '#0078d4') : '#0078d4';

  return (
    <>
      <div className="page-header">
        <h1>TakvenOps Board</h1>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
            <Plus size={13} /> New Work Item
          </button>
          <button
            className="btn btn-ghost"
            onClick={handleAutoAssign}
            disabled={autoAssigning}
            title="Auto-assign unassigned tasks"
          >
            <Wand2 size={14} /> {autoAssigning ? 'Assigning...' : 'Auto-Assign'}
          </button>
          <button
            className={`btn btn-ghost ${bulkMode ? 'btn-active' : ''}`}
            onClick={() => { setBulkMode(!bulkMode); setSelectedIds(new Set()); }}
            title="Bulk select"
          >
            <CheckSquare size={14} /> Bulk
          </button>
        </div>
      </div>

      {/* Quick Add — Natural Language */}
      <QuickAddBar onCreated={loadTasks} />

      {/* Filter toolbar */}
      <div className="toolbar">
        <select className="filter-select" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="">All Types</option>
          <option value="feature">Feature</option>
          <option value="bug">Bug</option>
          <option value="tech-debt">Tech Debt</option>
          <option value="research">Research</option>
          <option value="ops">Ops</option>
        </select>

        <select className="filter-select" value={filterAssignee} onChange={(e) => setFilterAssignee(e.target.value)}>
          <option value="">All Assignees</option>
          {uniqueAssignees.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>

        <div className="toolbar-divider" />

        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          {filtered.length} item{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Board */}
      <div className="board-wrapper">
        <DndContext
          sensors={sensors}
          collisionDetection={rectIntersection}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <div className="board-columns">
            {COLUMNS.map((col) => (
              <DroppableColumn
                key={col.id}
                id={col.id}
                label={col.label}
                tasks={tasksByStatus[col.id] || []}
                onTaskClick={setSelectedTask}
                bulkMode={bulkMode}
                selectedIds={selectedIds}
                onSelect={toggleSelect}
              />
            ))}
          </div>

          <DragOverlay dropAnimation={null}>
            {activeTask ? (
              <div className="card card-overlay" style={{ width: 240 }}>
                <div className="card-drag-handle" style={{ background: activeTypeColor }} />
                <div className="card-body">
                  <div className="card-title-row">
                    <div className="card-type-icon" style={{ background: activeTypeColor }}>
                      <svg width="10" height="10" viewBox="0 0 16 16" fill="white">
                        <rect x="2" y="2" width="12" height="12" rx="2" />
                      </svg>
                    </div>
                    <span className="card-title">{activeTask.title}</span>
                  </div>
                  <div className="card-assignee-row">
                    <span className="card-assignee-name">{activeTask.assignee || 'Unassigned'}</span>
                  </div>
                </div>
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>

        {/* Detail panel */}
        {selectedTask && (
          <TaskDetail
            task={selectedTask}
            onClose={() => setSelectedTask(null)}
            onUpdate={() => { loadTasks(); setSelectedTask(null); }}
          />
        )}
      </div>

      {showCreate && (
        <CreateTaskModal onClose={() => setShowCreate(false)} onCreated={loadTasks} />
      )}

      {bulkMode && (
        <BulkActionBar
          selectedIds={[...selectedIds]}
          onClear={() => setSelectedIds(new Set())}
          onDone={() => { setSelectedIds(new Set()); setBulkMode(false); loadTasks(); }}
        />
      )}
    </>
  );
}
