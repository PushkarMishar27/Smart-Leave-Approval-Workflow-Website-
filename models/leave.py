from models.database import get_db_connection
import datetime

class LeaveRequest:
    @staticmethod
    def create(user_id, leave_type, start_date, end_date, total_days, reason, ai_category, ai_confidence, document_path=None):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        
        # Generate Request Number
        year = datetime.datetime.now().strftime('%Y')
        cursor.execute("SELECT COUNT(*) as count FROM leave_requests")
        row = cursor.fetchone()
        count = (row['count'] if isinstance(row, dict) else row[0]) + 1
        request_number = f"LV-{year}-{count:03d}"
        
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            INSERT INTO leave_requests (request_number, user_id, leave_type, start_date, end_date, total_days, reason, ai_category, ai_confidence, status, current_level)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 'Pending', 'Faculty')
        """, (request_number, user_id, leave_type, start_date, end_date, total_days, reason, ai_category, ai_confidence))
        
        if db_type == 'sqlite':
            conn.commit()
            request_id = cursor.lastrowid
        else:
            request_id = cursor.lastrowid
            
        conn.close()
        return request_id, request_number

    @staticmethod
    def get_by_id(request_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            SELECT lr.*, u.name as user_name, u.employee_id, u.email as user_email, d.name as department_name, u.advisor_id
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.id
            JOIN departments d ON u.department_id = d.id
            WHERE lr.id = {placeholder}
        """, (request_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_user_id(user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            SELECT lr.*, u.name as user_name, d.name as department_name
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.id
            JOIN departments d ON u.department_id = d.id
            WHERE lr.user_id = {placeholder}
            ORDER BY lr.created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_pending_for_approver(role_name, department_id=None, approver_id=None):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        if role_name == 'Admin':
            cursor.execute("""
                SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name, u.advisor_id
                FROM leave_requests lr
                JOIN users u ON lr.user_id = u.id
                JOIN departments d ON u.department_id = d.id
                WHERE lr.status IN ('Pending', 'Forwarded') AND lr.current_level = 'Admin'
                ORDER BY lr.created_at ASC
            """)
        else: # Faculty/Approver
            placeholder = '%s' if db_type == 'mysql' else '?'
            if approver_id and department_id:
                cursor.execute(f"""
                    SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name, u.advisor_id
                    FROM leave_requests lr
                    JOIN users u ON lr.user_id = u.id
                    JOIN departments d ON u.department_id = d.id
                    WHERE lr.status = 'Pending' AND lr.current_level = 'Faculty' 
                      AND (u.advisor_id = {placeholder} OR u.department_id = {placeholder})
                    ORDER BY CASE WHEN u.advisor_id = {placeholder} THEN 0 ELSE 1 END, lr.created_at ASC
                """, (approver_id, department_id, approver_id))
            elif department_id:
                cursor.execute(f"""
                    SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name, u.advisor_id
                    FROM leave_requests lr
                    JOIN users u ON lr.user_id = u.id
                    JOIN departments d ON u.department_id = d.id
                    WHERE lr.status = 'Pending' AND lr.current_level = 'Faculty' AND u.department_id = {placeholder}
                    ORDER BY lr.created_at ASC
                """, (department_id,))
            else:
                cursor.execute("""
                    SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name, u.advisor_id
                    FROM leave_requests lr
                    JOIN users u ON lr.user_id = u.id
                    JOIN departments d ON u.department_id = d.id
                    WHERE lr.status = 'Pending' AND lr.current_level = 'Faculty'
                    ORDER BY lr.created_at ASC
                """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all_requests():
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.id
            JOIN departments d ON u.department_id = d.id
            ORDER BY lr.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def update_status(request_id, status, current_level='Completed'):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(f"""
            UPDATE leave_requests SET status = {placeholder}, current_level = {placeholder}, updated_at = {placeholder}
            WHERE id = {placeholder}
        """, (status, current_level, now, request_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()

class LeavePolicy:
    @staticmethod
    def get_all():
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leave_policies WHERE active = 1")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_type(leave_type):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"SELECT * FROM leave_policies WHERE leave_type = {placeholder} AND active = 1", (leave_type,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_policy(policy_id, allowance, max_days):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"UPDATE leave_policies SET allowance = {placeholder}, max_consecutive_days = {placeholder} WHERE id = {placeholder}", (allowance, max_days, policy_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()
        return True