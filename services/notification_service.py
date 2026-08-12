from models.database import get_db_connection

class NotificationService:
    @staticmethod
    def create(user_id, title, message, notif_type='info'):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            INSERT INTO notifications (user_id, title, message, type, read_status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 0)
        """, (user_id, title, message, notif_type))
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
            LIMIT 20
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def mark_as_read(notif_id, user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"UPDATE notifications SET read_status = 1 WHERE id = {placeholder} AND user_id = {placeholder}", (notif_id, user_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()

    @staticmethod
    def mark_all_as_read(user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"UPDATE notifications SET read_status = 1 WHERE user_id = {placeholder}", (user_id,))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()
