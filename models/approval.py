from models.database import get_db_connection
import datetime

class ApprovalStep:
    @staticmethod
    def add_step(leave_request_id, approver_id, level, status, comment=None):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(f"""
            INSERT INTO approval_steps (leave_request_id, approver_id, level, status, comment, action_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """, (leave_request_id, approver_id, level, status, comment, now))
        if db_type == 'sqlite':
            conn.commit()
            step_id = cursor.lastrowid
        else:
            step_id = cursor.lastrowid
        conn.close()
        return step_id

    @staticmethod
    def get_steps_for_request(leave_request_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            SELECT ast.*, u.name as approver_name, r.name as approver_role
            FROM approval_steps ast
            JOIN users u ON ast.approver_id = u.id
            JOIN roles r ON u.role_id = r.id
            WHERE ast.leave_request_id = {placeholder}
            ORDER BY ast.action_at ASC
        """, (leave_request_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
