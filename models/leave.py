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
            INSERT INTO leave_requests (request_number, user_id, leave_type, start_date, end_date, total_days, reason, ai_category, ai_confidence, status, current_level, document_path)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 'Pending', 'Faculty', {placeholder})
        """, (request_number, user_id, leave_type, start_date, end_date, total_days, reason, ai_category, ai_confidence, document_path))
        
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
            SELECT lr.*, u.name as user_name, u.employee_id, u.email as user_email, d.name as department_name
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.id
            JOIN departments d ON u.department_id = d.id
            WHERE lr.id = {placeholder}
        """, (request_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_user_requests(user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            SELECT * FROM leave_requests
            WHERE user_id = {placeholder}
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_pending_for_approver(role_name, department_id=None):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        if role_name == 'Admin':
            cursor.execute("""
                SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name
                FROM leave_requests lr
                JOIN users u ON lr.user_id = u.id
                JOIN departments d ON u.department_id = d.id
                WHERE lr.status IN ('Pending', 'Forwarded') AND lr.current_level = 'Admin'
                ORDER BY lr.created_at ASC
            """)
        else: # Faculty/Approver
            placeholder = '%s' if db_type == 'mysql' else '?'
            if department_id:
                cursor.execute(f"""
                    SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name
                    FROM leave_requests lr
                    JOIN users u ON lr.user_id = u.id
                    JOIN departments d ON u.department_id = d.id
                    WHERE lr.status = 'Pending' AND lr.current_level = 'Faculty' AND u.department_id = {placeholder}
                    ORDER BY lr.created_at ASC
                """, (department_id,))
            else:
                cursor.execute("""
                    SELECT lr.*, u.name as user_name, u.employee_id, d.name as department_name
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
    def update_status(request_id, status, current_level=None):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        if current_level:
            cursor.execute(f"UPDATE leave_requests SET status = {placeholder}, current_level = {placeholder} WHERE id = {placeholder}", (status, current_level, request_id))
        else:
            cursor.execute(f"UPDATE leave_requests SET status = {placeholder} WHERE id = {placeholder}", (status, request_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()

    @staticmethod
    def get_user_leave_balance(user_id):
        """
        Calculates leave allowances, used days (only APPROVED leaves), pending days, and remaining balance.
        """
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        
        # Get total allocated allowance from policies
        cursor.execute("SELECT SUM(allowance) as total_allowance FROM leave_policies WHERE active = 1")
        row = cursor.fetchone()
        allocated = (row['total_allowance'] if isinstance(row, dict) else row[0]) or 35
        
        # Approved used days
        cursor.execute(f"""
            SELECT SUM(total_days) as used_days FROM leave_requests
            WHERE user_id = {placeholder} AND status = 'Approved'
        """, (user_id,))
        row_used = cursor.fetchone()
        used = (row_used['used_days'] if isinstance(row_used, dict) else row_used[0]) or 0
        
        # Pending days
        cursor.execute(f"""
            SELECT SUM(total_days) as pending_days FROM leave_requests
            WHERE user_id = {placeholder} AND status IN ('Pending', 'Forwarded')
        """, (user_id,))
        row_pending = cursor.fetchone()
        pending = (row_pending['pending_days'] if isinstance(row_pending, dict) else row_pending[0]) or 0
        
        # Approved count this year
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM leave_requests
            WHERE user_id = {placeholder} AND status = 'Approved'
        """, (user_id,))
        row_approved_count = cursor.fetchone()
        approved_count = (row_approved_count['count'] if isinstance(row_approved_count, dict) else row_approved_count[0]) or 0
        
        conn.close()
        
        remaining = allocated - used
        return {
            'allocated': int(allocated),
            'used': int(used),
            'pending': int(pending),
            'remaining': int(remaining),
            'approved_count': int(approved_count)
        }

class LeavePolicy:
    @staticmethod
    def get_all():
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT lp.*, d.name as department_name
            FROM leave_policies lp
            LEFT JOIN departments d ON lp.department_id = d.id
            ORDER BY lp.id ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def update(policy_id, allowance, max_consecutive_days, active):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            UPDATE leave_policies SET allowance = {placeholder}, max_consecutive_days = {placeholder}, active = {placeholder}
            WHERE id = {placeholder}
        """, (allowance, max_consecutive_days, active, policy_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()
        return True
