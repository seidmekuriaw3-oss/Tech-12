"""
Notification Service for SEMIRA FASHION
In-app notifications stored in DB for both customers and admins.
"""

from database.db import get_db
import logging
logger = logging.getLogger(__name__)


# ── User (Customer) Notifications ──────────────────────────────────────

def notify_user(user_id, title, body, type='info', link=''):
    """Insert a notification into the user's inbox."""
    if not user_id:
        return False
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO user_notifications (user_id, title, body, type, link) VALUES (%s, %s, %s, %s, %s)",
            (user_id, title, body, type, link or '')
        )
        db.commit()
        return True
    except Exception as e:
        logger.error(f"[notify_user] error: {e}")
        return False


def get_user_notifications(user_id, limit=50):
    """Fetch notifications for a user, newest first."""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, title, body, type, link, is_read, created_at "
            "FROM user_notifications WHERE user_id = %s "
            "ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        rows = cur.fetchall()
        result = []
        for r in (rows or []):
            result.append({
                'id':         r['id'],
                'title':      r['title'],
                'body':       r['body'],
                'type':       r['type'],
                'link':       r['link'] or '',
                'is_read':    bool(r['is_read']),
                'created_at': str(r['created_at'])[:16] if r['created_at'] else '',
            })
        return result
    except Exception as e:
        logger.error(f"[get_user_notifications] error: {e}")
        return []


def get_user_unread_count(user_id):
    """Return number of unread notifications for a user."""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM user_notifications WHERE user_id = %s AND is_read = 0",
            (user_id,)
        )
        row = cur.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def mark_user_notifications_read(user_id, notif_id=None):
    """Mark one or all notifications as read for a user."""
    try:
        db = get_db()
        cur = db.cursor()
        if notif_id:
            cur.execute(
                "UPDATE user_notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
                (notif_id, user_id)
            )
        else:
            cur.execute(
                "UPDATE user_notifications SET is_read = 1 WHERE user_id = %s",
                (user_id,)
            )
        db.commit()
        return True
    except Exception as e:
        logger.error(f"[mark_user_notifications_read] error: {e}")
        return False


# ── Admin Alerts ────────────────────────────────────────────────────────

def notify_admin(title, body, type='info', link='', ref_order_id=None, ref_user_id=None):
    """Insert an alert into the admin inbox."""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO admin_alerts (title, body, type, link, ref_order_id, ref_user_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (title, body, type, link or '', ref_order_id, ref_user_id)
        )
        db.commit()
        return True
    except Exception as e:
        logger.error(f"[notify_admin] error: {e}")
        return False


def get_admin_alerts(limit=60):
    """Fetch admin alerts, newest first."""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, title, body, type, link, ref_order_id, ref_user_id, is_read, created_at "
            "FROM admin_alerts ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        rows = cur.fetchall()
        result = []
        for r in (rows or []):
            result.append({
                'id':           r['id'],
                'title':        r['title'],
                'body':         r['body'],
                'type':         r['type'],
                'link':         r['link'] or '',
                'ref_order_id': r['ref_order_id'],
                'ref_user_id':  r['ref_user_id'],
                'is_read':      bool(r['is_read']),
                'created_at':   str(r['created_at'])[:16] if r['created_at'] else '',
            })
        return result
    except Exception as e:
        logger.error(f"[get_admin_alerts] error: {e}")
        return []


def get_admin_unread_count():
    """Return number of unread admin alerts."""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT COUNT(*) FROM admin_alerts WHERE is_read = 0")
        row = cur.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def mark_admin_alerts_read(alert_id=None):
    """Mark one or all admin alerts as read."""
    try:
        db = get_db()
        cur = db.cursor()
        if alert_id:
            cur.execute("UPDATE admin_alerts SET is_read = 1 WHERE id = %s", (alert_id,))
        else:
            cur.execute("UPDATE admin_alerts SET is_read = 1")
        db.commit()
        return True
    except Exception as e:
        logger.error(f"[mark_admin_alerts_read] error: {e}")
        return False


# ── Legacy stubs (kept for import compatibility) ────────────────────────

class NotificationService:
    @staticmethod
    def send_push_notification(title, body, data=None, target='all', user_id=None):
        return False

    @staticmethod
    def send_email_notification(to_email, subject, body, html_body=None):
        return False

    @staticmethod
    def send_order_notification(order_id, status):
        return False

    @staticmethod
    def send_admin_alert(title, body):
        return False


def send_push_notification(title, body, data=None, target='all', user_id=None):
    return False


def send_email_notification(to_email, subject, body, html_body=None):
    return False
