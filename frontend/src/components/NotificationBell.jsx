import { useState, useEffect, useRef } from 'react';
import { Bell, Check, CheckCheck } from 'lucide-react';
import { getNotifications, getUnreadCount, markNotificationRead, markAllNotificationsRead } from '../api';
import './NotificationBell.css';

export default function NotificationBell() {
  const [count, setCount] = useState(0);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);

  const fetchCount = async () => {
    try {
      const data = await getUnreadCount();
      setCount(data.count || 0);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleOpen = async () => {
    setOpen((v) => !v);
    if (!open) {
      setLoading(true);
      try {
        setNotifications(await getNotifications());
      } catch { /* ignore */ }
      setLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: 1 } : n));
      setCount((c) => Math.max(0, c - 1));
    } catch { /* ignore */ }
  };

  const handleMarkAll = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: 1 })));
      setCount(0);
    } catch { /* ignore */ }
  };

  const typeIcons = {
    assigned: 'Assigned',
    commented: 'Comment',
    status_changed: 'Moved',
  };

  return (
    <div className="notif-bell-wrapper" ref={ref}>
      <button className="notif-bell-btn" onClick={handleOpen} title="Notifications">
        <Bell size={16} />
        {count > 0 && <span className="notif-badge">{count > 9 ? '9+' : count}</span>}
      </button>

      {open && (
        <div className="notif-dropdown">
          <div className="notif-dropdown-header">
            <span>Notifications</span>
            {count > 0 && (
              <button className="notif-mark-all" onClick={handleMarkAll} title="Mark all read">
                <CheckCheck size={14} /> Mark all read
              </button>
            )}
          </div>
          <div className="notif-dropdown-body">
            {loading && <div className="notif-empty">Loading...</div>}
            {!loading && notifications.length === 0 && (
              <div className="notif-empty">No notifications yet</div>
            )}
            {!loading && notifications.map((n) => (
              <div key={n.id} className={`notif-item ${n.read ? '' : 'notif-unread'}`}>
                <div className="notif-item-content">
                  <span className="notif-type-badge">{typeIcons[n.type] || n.type}</span>
                  <span className="notif-message">{n.message}</span>
                  <span className="notif-time">{new Date(n.created_at).toLocaleDateString()}</span>
                </div>
                {!n.read && (
                  <button className="notif-read-btn" onClick={() => handleMarkRead(n.id)} title="Mark read">
                    <Check size={12} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
