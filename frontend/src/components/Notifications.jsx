// components/Notifications.jsx (New: Component to display notifications)
import React, { useState, useEffect } from 'react';
import { BASE_URLS } from '../api/api';

function Notifications({ user }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) return;
    fetchNotifications();
  }, [user]);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BASE_URLS.user}/api/notifications?email=${encodeURIComponent(user.email)}`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      } else {
        setError('Failed to fetch notifications');
      }
    } catch (err) {
      setError('Error fetching notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (messageId) => {
    try {
      const response = await fetch(`${BASE_URLS.user}/api/mark_read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_id: messageId })
      });
      if (response.ok) {
        // Update local state
        setNotifications(notifications.map(n => 
          n.message_id === messageId ? { ...n, is_read: true } : n
        ));
      }
    } catch (err) {
      console.error('Error marking as read:', err);
    }
  };

  const markAllAsRead = async () => {
    const unread = notifications.filter(n => !n.is_read);
    for (const notif of unread) {
      await markAsRead(notif.message_id);
    }
  };

  if (loading) return <div className="text-center mt-5">Loading notifications...</div>;
  if (error) return <div className="alert alert-danger text-center mt-5">{error}</div>;

  const getTypeClass = (type) => {
    switch (type) {
      case 'approval': return 'text-success';
      case 'rejection': return 'text-danger';
      case 'bank_submitted': return 'text-info';
      default: return 'text-primary';
    }
  };

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2>Notifications</h2>
        {/* {notifications.some(n => !n.is_read) && (
          <button className="btn btn-primary" onClick={markAllAsRead}>
            Mark All as Read
          </button>
        )} */}
      </div>
      {notifications.length === 0 ? (
        <div className="alert alert-info text-center">No notifications yet.</div>
      ) : (
        <div className="list-group">
          {notifications.map((notif) => (
            <div
              key={notif.message_id}
              className={`list-group-item list-group-item-action ${
                !notif.is_read ? 'list-group-item-info' : ''
              }`}
            >
              <div className="d-flex w-100 justify-content-between">
                <h5 className={`mb-1 ${getTypeClass(notif.notification_type)}`}>
                  {notif.notification_type === 'approval' && '✅ Approved: '}
                  {notif.notification_type === 'rejection' && '❌ Rejected: '}
                  {notif.notification_type === 'bank_submitted' && '💳 Bank Submitted: '}
                  {notif.message}
                </h5>
                <small>{new Date(notif.sent_at).toLocaleDateString()}</small>
              </div>
              <p className="mb-1">{notif.message}</p>
              {!notif.is_read && (
                <button
                  className="btn btn-sm btn-outline-primary"
                  onClick={() => markAsRead(notif.message_id)}
                >
                  Mark as Read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Notifications;