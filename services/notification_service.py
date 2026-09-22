from models.database import get_db_connection

class NotificationService:
    @staticmethod
    def send_notification(user_id, title, message):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            INSERT INTO notifications (user_id, title, message, is_read)
            VALUES ({placeholder}, {placeholder}, {placeholder}, 0)
        """, (user_id, title, message))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()

    @staticmethod
    def get_user_notifications(user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            SELECT * FROM notifications
            WHERE user_id = {placeholder}
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def mark_as_read(notif_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"UPDATE notifications SET is_read = 1 WHERE id = {placeholder}", (notif_id,))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()
