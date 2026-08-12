import sqlite3
import pymysql
import os
from config import Config
from werkzeug.security import generate_password_hash

def get_db_connection():
    """
    Returns a database connection.
    Tries MySQL connection first if configured, else defaults to SQLite DB.
    """
    try:
        if os.environ.get('USE_MYSQL') == 'true':
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            return conn, 'mysql'
    except Exception as e:
        print(f"[Database] MySQL connection failed ({e}), falling back to SQLite.")

    # SQLite Fallback
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'

def init_db():
    """
    Initializes SQLite schema and populates seed data if database file does not exist or is empty.
    """
    db_path = Config.SQLITE_DB_PATH
    conn, db_type = get_db_connection()
    
    if db_type == 'sqlite':
        cursor = conn.cursor()
        
        # Enable Foreign Keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 1. Departments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                code TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. Roles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')

        # 3. Permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')

        # 4. Role Permissions Mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
            )
        ''')

        # 5. Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                department_id INTEGER NOT NULL,
                mfa_secret TEXT DEFAULT NULL,
                mfa_enabled INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (role_id) REFERENCES roles(id),
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        ''')

        # 6. Leave Policies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leave_type TEXT NOT NULL,
                allowance INTEGER NOT NULL DEFAULT 12,
                max_consecutive_days INTEGER NOT NULL DEFAULT 5,
                department_id INTEGER NULL,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE
            )
        ''')

        # 7. Leave Requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                total_days INTEGER NOT NULL,
                reason TEXT NOT NULL,
                ai_category TEXT DEFAULT 'Personal',
                ai_confidence REAL DEFAULT 0.0,
                status TEXT DEFAULT 'Pending',
                current_level TEXT DEFAULT 'Faculty',
                document_path TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # 8. Approval Steps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leave_request_id INTEGER NOT NULL,
                approver_id INTEGER NOT NULL,
                level TEXT NOT NULL,
                status TEXT NOT NULL,
                comment TEXT DEFAULT NULL,
                action_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (leave_request_id) REFERENCES leave_requests(id) ON DELETE CASCADE,
                FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # 9. Notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                read_status INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # 10. Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NULL,
                action TEXT NOT NULL,
                entity TEXT NOT NULL,
                entity_id INTEGER NULL,
                metadata TEXT DEFAULT NULL,
                ip_address TEXT DEFAULT '127.0.0.1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()

        # Seed data if users table is empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            seed_sqlite_db(cursor, conn)

        conn.close()

def seed_sqlite_db(cursor, conn):
    """
    Populates SQLite DB with realistic seed data.
    """
    # 1. Departments
    departments = [
        (1, 'Computer Science', 'CS'),
        (2, 'Information Technology', 'IT'),
        (3, 'Electronics & Comm.', 'ECE'),
        (4, 'Mechanical Eng.', 'ME'),
        (5, 'Administration', 'ADMIN')
    ]
    cursor.executemany("INSERT INTO departments (id, name, code) VALUES (?, ?, ?)", departments)

    # 2. Roles
    roles = [
        (1, 'Student/Employee', 'Can submit leave applications and track leave status/balances.'),
        (2, 'Faculty/Approver', 'Can review, approve, reject, or forward assigned leave applications.'),
        (3, 'Admin', 'Full administrative control over users, policies, workflows, and audit logs.')
    ]
    cursor.executemany("INSERT INTO roles (id, name, description) VALUES (?, ?, ?)", roles)

    # 3. Permissions
    permissions = [
        (1, 'apply_leave', 'Submit new leave requests'),
        (2, 'view_own_requests', 'View personal leave requests & balance'),
        (3, 'review_assigned_leaves', 'Approve, reject, or forward pending assigned leaves'),
        (4, 'manage_users', 'Add, edit, or disable user accounts'),
        (5, 'manage_policies', 'Modify leave allowances and threshold rules'),
        (6, 'view_audit_logs', 'View and export system audit trail logs')
    ]
    cursor.executemany("INSERT INTO permissions (id, name, description) VALUES (?, ?, ?)", permissions)

    # 4. Role Permissions
    role_permissions = [
        (1, 1), (1, 2),
        (2, 3), (2, 2),
        (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6)
    ]
    cursor.executemany("INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)", role_permissions)

    # 5. Users
    pwd_hash = generate_password_hash('password123')
    users = [
        (1, 'STU1001', 'Alex Mercer', 'alex.mercer@smartleave.edu', pwd_hash, 1, 1, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
        (2, 'STU1002', 'Sophia Chen', 'sophia.chen@smartleave.edu', pwd_hash, 1, 1, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
        (3, 'FAC2001', 'Dr. Robert Vance', 'robert.vance@smartleave.edu', pwd_hash, 2, 1, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
        (4, 'FAC2002', 'Prof. Elena Rostova', 'elena.rostova@smartleave.edu', pwd_hash, 2, 2, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
        (5, 'ADM3001', 'Administrator Marcus', 'admin@smartleave.edu', pwd_hash, 3, 5, 'JBSWY3DPEHPK3PXP', 1, 'Active')
    ]
    cursor.executemany("""
        INSERT INTO users (id, employee_id, name, email, password_hash, role_id, department_id, mfa_secret, mfa_enabled, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, users)

    # 6. Leave Policies
    policies = [
        (1, 'Casual Leave', 12, 3, 1, 1),
        (2, 'Medical Leave', 10, 7, 1, 1),
        (3, 'Personal Leave', 8, 4, 1, 1),
        (4, 'Emergency Leave', 5, 2, 1, 1)
    ]
    cursor.executemany("INSERT INTO leave_policies (id, leave_type, allowance, max_consecutive_days, department_id, active) VALUES (?, ?, ?, ?, ?, ?)", policies)

    # 7. Leave Requests
    leaves = [
        (101, 'LV-2026-001', 1, 'Medical Leave', '2026-08-12', '2026-08-14', 3, 'Severe viral fever and doctor recommended complete bed rest for 3 days.', 'Medical', 96.4, 'Pending', 'Faculty'),
        (102, 'LV-2026-002', 1, 'Casual Leave', '2026-07-10', '2026-07-11', 2, 'Attending sibling wedding ceremony in hometown.', 'Personal', 91.2, 'Approved', 'Faculty'),
        (103, 'LV-2026-003', 2, 'Emergency Leave', '2026-08-15', '2026-08-18', 4, 'Family medical emergency requiring immediate travel.', 'Urgent', 94.8, 'Forwarded', 'Admin')
    ]
    cursor.executemany("""
        INSERT INTO leave_requests (id, request_number, user_id, leave_type, start_date, end_date, total_days, reason, ai_category, ai_confidence, status, current_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, leaves)

    # 8. Approval Steps
    steps = [
        (1, 102, 3, 'Faculty', 'Approved', 'Approved as requested. Stay safe.', '2026-07-09 10:30:00'),
        (2, 103, 3, 'Faculty', 'Forwarded', 'Forwarding to Admin since duration exceeds 3 consecutive days.', '2026-08-10 08:15:00')
    ]
    cursor.executemany("INSERT INTO approval_steps (id, leave_request_id, approver_id, level, status, comment, action_at) VALUES (?, ?, ?, ?, ?, ?, ?)", steps)

    # 9. Notifications
    notifs = [
        (1, 1, 'Leave Request Approved', 'Your leave request #LV-2026-002 has been approved by Dr. Robert Vance.', 'success', 1),
        (2, 1, 'Leave Under Review', 'Your leave request #LV-2026-001 is awaiting review by Dr. Robert Vance.', 'info', 0),
        (3, 3, 'Approval Required', 'New leave request #LV-2026-001 from Alex Mercer requires your review.', 'warning', 0)
    ]
    cursor.executemany("INSERT INTO notifications (id, user_id, title, message, type, read_status) VALUES (?, ?, ?, ?, ?, ?)", notifs)

    # 10. Audit Logs
    logs = [
        (1, 1, 'USER_LOGIN', 'users', 1, '{"method": "TOTP_MFA", "status": "Success"}', '127.0.0.1'),
        (2, 1, 'SUBMIT_LEAVE', 'leave_requests', 101, '{"type": "Medical Leave", "days": 3}', '127.0.0.1'),
        (3, 3, 'APPROVE_LEAVE', 'leave_requests', 102, '{"approver": "Dr. Robert Vance", "level": "Faculty"}', '127.0.0.1')
    ]
    cursor.executemany("INSERT INTO audit_logs (id, user_id, action, entity, entity_id, metadata, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)", logs)

    conn.commit()
