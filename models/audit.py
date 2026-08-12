from models.database import get_db_connection
import json

class AuditLog:
    @staticmethod
    def log(user_id, action, entity, entity_id=None, metadata=None, ip_address='127.0.0.1'):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        meta_str = json.dumps(metadata) if isinstance(metadata, dict) else metadata
        cursor.execute(f"""
            INSERT INTO audit_logs (user_id, action, entity, entity_id, metadata, ip_address)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """, (user_id, action, entity, entity_id, meta_str, ip_address))
        if db_type == 'sqlite':
            conn.commit()
        conn.close()

    @staticmethod
    def get_all(limit=100):
        conn, db_type = get_db_connection()
        cursor = conn.cursor()
        placeholder = '%s' if db_type == 'mysql' else '?'
        cursor.execute(f"""
            SELECT al.*, u.name as user_name, u.employee_id, r.name as role_name
            FROM audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY al.created_at DESC
            LIMIT {limit}
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
