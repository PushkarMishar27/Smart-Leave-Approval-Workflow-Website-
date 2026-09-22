from models.database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

class User:
    @staticmethod
    def get_by_id(user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        if db_type == 'mysql':
            cursor.execute("""
                SELECT u.*, r.name as role_name, d.name as department_name, d.code as department_code, adv.name as advisor_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                JOIN departments d ON u.department_id = d.id
                LEFT JOIN users adv ON u.advisor_id = adv.id
                WHERE u.id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT u.*, r.name as role_name, d.name as department_name, d.code as department_code, adv.name as advisor_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                JOIN departments d ON u.department_id = d.id
                LEFT JOIN users adv ON u.advisor_id = adv.id
                WHERE u.id = ?
            """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_employee_id(employee_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            SELECT u.*, r.name as role_name, d.name as department_name, d.code as department_code, adv.name as advisor_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            JOIN departments d ON u.department_id = d.id
            LEFT JOIN users adv ON u.advisor_id = adv.id
            WHERE u.employee_id = {placeholder}
        """, (employee_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def authenticate(employee_id, password):
        user = User.get_by_employee_id(employee_id)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    @staticmethod
    def update_last_login(user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(f"UPDATE users SET last_login = {placeholder} WHERE id = {placeholder}", (now, user_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()

    @staticmethod
    def update_mfa_secret(user_id, secret, enabled=1):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"UPDATE users SET mfa_secret = {placeholder}, mfa_enabled = {placeholder} WHERE id = {placeholder}", (secret, enabled, user_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()

    @staticmethod
    def get_all_users():
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.employee_id, u.name, u.email, u.status, u.mfa_enabled, u.last_login, u.created_at, u.advisor_id,
                   r.name as role_name, r.id as role_id, d.name as department_name, d.id as department_id, adv.name as advisor_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            JOIN departments d ON u.department_id = d.id
            LEFT JOIN users adv ON u.advisor_id = adv.id
            ORDER BY u.id ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_faculty_members():
        users = User.get_all_users()
        return [u for u in users if u['role_name'] == 'Faculty/Approver']

    @staticmethod
    def get_students():
        users = User.get_all_users()
        return [u for u in users if u['role_name'] == 'Student/Employee']

    @staticmethod
    def assign_faculty_to_students(faculty_id, student_ids):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        for sid in student_ids:
            cursor.execute(f"UPDATE users SET advisor_id = {placeholder} WHERE id = {placeholder}", (faculty_id if faculty_id else None, sid))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()
        return True

    @staticmethod
    def create_user(employee_id, name, email, password, role_id, department_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        pwd_hash = generate_password_hash(password)
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            INSERT INTO users (employee_id, name, email, password_hash, role_id, department_id, mfa_secret, mfa_enabled, status)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 'JBSWY3DPEHPK3PXP', 1, 'Active')
        """, (employee_id, name, email, pwd_hash, role_id, department_id))
        if db_type == 'sqlite':
            conn.commit()
            new_id = cursor.lastrowid
        else:
            new_id = cursor.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def update_user(user_id, name, email, role_id, department_id, status):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            UPDATE users SET name = {placeholder}, email = {placeholder}, role_id = {placeholder}, department_id = {placeholder}, status = {placeholder}
            WHERE id = {placeholder}
        """, (name, email, role_id, department_id, status, user_id))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete_user(user_id):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        if db_type == 'sqlite':
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("DELETE FROM leave_requests WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM approval_steps WHERE approver_id = ?", (user_id,))
            cursor.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        else:
            cursor.execute(f"DELETE FROM users WHERE id = {placeholder}", (user_id,))
        conn.close()
        return True