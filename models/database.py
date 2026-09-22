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

        # 4. Role Permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                role_id INTEGER,
                permission_id INTEGER,
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
                mfa_secret TEXT DEFAULT 'JBSWY3DPEHPK3PXP',
                mfa_enabled INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Active',
                advisor_id INTEGER NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles(id),
                FOREIGN KEY (department_id) REFERENCES departments(id),
                FOREIGN KEY (advisor_id) REFERENCES users(id)
            )
        ''')

        # Check if users table is populated
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        if user_count == 0:
            # Seed Departments
            departments = [
                (1, 'Computer Science & Engineering', 'CSE'),
                (2, 'Information Technology', 'IT'),
                (3, 'Electronics & Communication', 'ECE'),
                (4, 'Electrical Engineering', 'EE'),
                (5, 'Mechanical Engineering', 'ME'),
                (6, 'Administration Control', 'ADMIN')
            ]
            cursor.executemany("INSERT OR IGNORE INTO departments (id, name, code) VALUES (?, ?, ?)", departments)

            # Seed Roles
            roles = [
                (1, 'Student/Employee', 'Standard user applying for leaves'),
                (2, 'Faculty/Approver', 'Faculty/Approver with decision authority'),
                (3, 'Admin', 'Administrator with full system control')
            ]
            cursor.executemany("INSERT OR IGNORE INTO roles (id, name, description) VALUES (?, ?, ?)", roles)

            # Seed Permissions
            permissions = [
                (1, 'apply_leave', 'Create and submit leave applications'),
                (2, 'view_self_leaves', 'View history of personal leave requests'),
                (3, 'approve_leave', 'Approve, reject, or forward leave requests'),
                (4, 'manage_users', 'Add, edit, or disable user accounts'),
                (5, 'manage_policies', 'Modify leave allowances and threshold rules'),
                (6, 'view_audit_logs', 'View and export system audit trail logs')
            ]
            cursor.executemany("INSERT OR IGNORE INTO permissions (id, name, description) VALUES (?, ?, ?)", permissions)

            # Seed Users (Admin Only)
            pwd_hash = generate_password_hash('password123')
            users = [
                (8, 'ADM3001', 'Pushkar Mishra', 'pushkar.mishra@smartleave.edu.in', pwd_hash, 3, 6, 'JBSWY3DPEHPK3PXP', 1, 'Active', None)
            ]
            cursor.executemany("""
                INSERT OR IGNORE INTO users (id, employee_id, name, email, password_hash, role_id, department_id, mfa_secret, mfa_enabled, status, advisor_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, users)

        # 6. Leave Policies
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leave_type TEXT NOT NULL,
                allowance INTEGER NOT NULL,
                max_consecutive_days INTEGER NOT NULL,
                department_id INTEGER,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        ''')
        cursor.execute("SELECT COUNT(*) FROM leave_policies")
        if cursor.fetchone()[0] == 0:
            policies = [
                ('Casual Leave', 12, 3, 1),
                ('Medical Leave', 15, 10, 1),
                ('Duty Leave', 10, 5, 1),
                ('Earned Leave', 20, 14, 1),
                ('Special Leave', 5, 3, 1)
            ]
            cursor.executemany("INSERT INTO leave_policies (leave_type, allowance, max_consecutive_days, active) VALUES (?, ?, ?, ?)", policies)

        # 7. Leave Requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                total_days INTEGER NOT NULL,
                reason TEXT NOT NULL,
                ai_category TEXT DEFAULT 'Personal',
                ai_confidence REAL DEFAULT 0.85,
                status TEXT DEFAULT 'Pending',
                current_level TEXT DEFAULT 'Faculty',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # 8. Approval Steps
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                approver_id INTEGER NOT NULL,
                level TEXT NOT NULL,
                status TEXT NOT NULL,
                comments TEXT,
                action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES leave_requests(id) ON DELETE CASCADE,
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
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # 10. Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                target_id INTEGER,
                details TEXT,
                ip_address TEXT DEFAULT '127.0.0.1',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
    conn.close()