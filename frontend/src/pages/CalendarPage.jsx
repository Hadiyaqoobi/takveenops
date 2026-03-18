import { useState, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { getCalendarTasks } from '../api';
import './CalendarPage.css';

const TYPE_COLORS = {
  feature: '#773b93', bug: '#cc293d', 'tech-debt': '#ca5010',
  research: '#0078d4', ops: '#8a8886',
};

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [tasksByDate, setTasksByDate] = useState({});
  const [selectedDay, setSelectedDay] = useState(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;

  useEffect(() => {
    getCalendarTasks(monthStr)
      .then((res) => setTasksByDate(res.tasks_by_date || {}))
      .catch(console.error);
  }, [monthStr]);

  const prevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(year, month + 1, 1));

  const monthName = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });

  // Build calendar grid
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = [];

  // Empty cells for padding
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  const dayStr = (d) => `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

  const selectedTasks = selectedDay ? (tasksByDate[dayStr(selectedDay)] || []) : [];

  return (
    <>
      <div className="page-header">
        <h1><Calendar size={16} /> Calendar</h1>
      </div>

      <div className="page-body">
        <div className="cal-nav">
          <button className="btn btn-ghost" onClick={prevMonth}><ChevronLeft size={16} /></button>
          <h2 className="cal-month">{monthName}</h2>
          <button className="btn btn-ghost" onClick={nextMonth}><ChevronRight size={16} /></button>
        </div>

        <div className="cal-grid">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d) => (
            <div key={d} className="cal-day-header">{d}</div>
          ))}

          {cells.map((day, i) => {
            if (!day) return <div key={`e${i}`} className="cal-cell cal-empty" />;
            const key = dayStr(day);
            const dayTasks = tasksByDate[key] || [];
            const isToday =
              day === new Date().getDate() &&
              month === new Date().getMonth() &&
              year === new Date().getFullYear();
            const isSelected = selectedDay === day;

            return (
              <div
                key={key}
                className={`cal-cell ${isToday ? 'cal-today' : ''} ${isSelected ? 'cal-selected' : ''} ${dayTasks.length ? 'cal-has-tasks' : ''}`}
                onClick={() => setSelectedDay(day)}
              >
                <span className="cal-day-num">{day}</span>
                <div className="cal-chips">
                  {dayTasks.slice(0, 3).map((t) => (
                    <div
                      key={t.id}
                      className="cal-chip"
                      style={{ background: TYPE_COLORS[t.type] || '#0078d4' }}
                      title={`${t.id}: ${t.title}`}
                    />
                  ))}
                  {dayTasks.length > 3 && (
                    <span className="cal-more">+{dayTasks.length - 3}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Day detail panel */}
        {selectedDay && (
          <div className="cal-detail">
            <h3>{dayStr(selectedDay)}</h3>
            {selectedTasks.length === 0 && <div className="myday-empty">No tasks due this day</div>}
            {selectedTasks.map((t) => (
              <div key={t.id} className="cal-detail-task">
                <div className="cal-detail-type" style={{ background: TYPE_COLORS[t.type] || '#888' }} />
                <span className="cal-detail-id">{t.id}</span>
                <span className="cal-detail-title">{t.title}</span>
                <span className={`badge badge-${t.priority?.toLowerCase()}`}>{t.priority}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
