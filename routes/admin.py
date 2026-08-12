from flask import Blueprint, request, jsonify, session, Response
from models.user import User
from models.leave import LeaveRequest, LeavePolicy
from models.audit import AuditLog
import csv
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def require_admin():
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return None
    return user

@admin_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    users = User.get_all_users()
    all_leaves = LeaveRequest.get_all_requests()
    audit_logs = AuditLog.get_all(limit=50)
    policies = LeavePolicy.get_all()

    # Metrics
    total_users = len(users)
    active_users = sum(1 for u in users if u['status'] == 'Active')
    pending_leaves = sum(1 for l in all_leaves if l['status'] in ('Pending', 'Forwarded'))
    approved_leaves = sum(1 for l in all_leaves if l['status'] == 'Approved')
    rejected_leaves = sum(1 for l in all_leaves if l['status'] == 'Rejected')

    # Distribution by category for Doughnut Chart
    category_counts = {'Medical': 0, 'Personal': 0, 'Urgent': 0}
    for l in all_leaves:
        cat = l.get('ai_category', 'Personal')
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Department statistics
    dept_counts = {}
    for l in all_leaves:
        dept = l.get('department_name', 'General')
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    return jsonify({
        'success': True,
        'user': {'name': user['name'], 'role': user['role_name']},
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'pending_leaves': pending_leaves,
            'approved_leaves': approved_leaves,
            'rejected_leaves': rejected_leaves,
            'departments_count': len(dept_counts),
            'audit_events_count': len(audit_logs)
        },
        'charts': {
            'categories': category_counts,
            'status': {
                'Pending': pending_leaves,
                'Approved': approved_leaves,
                'Rejected': rejected_leaves
            },
            'departments': dept_counts
        },
        'recent_leaves': all_leaves[:10],
        'recent_audit': audit_logs[:10]
    })

@admin_bp.route('/users', methods=['GET', 'POST', 'PUT'])
def manage_users():
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    if request.method == 'GET':
        users = User.get_all_users()
        return jsonify({'success': True, 'users': users})

    elif request.method == 'POST':
        data = request.json or {}
        emp_id = data.get('employee_id', '').strip()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', 'password123')
        role_id = int(data.get('role_id', 1))
        department_id = int(data.get('department_id', 1))

        if not emp_id or not name or not email:
            return jsonify({'success': False, 'message': 'Please provide Employee ID, Name, and Email.'}), 400

        try:
            new_id = User.create_user(emp_id, name, email, password, role_id, department_id)
            AuditLog.log(user['id'], 'CREATE_USER', 'users', new_id, {'employee_id': emp_id, 'name': name})
            return jsonify({'success': True, 'message': f'User {name} ({emp_id}) created successfully.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error creating user: {str(e)}'}), 400

    elif request.method == 'PUT':
        data = request.json or {}
        user_id = data.get('id')
        name = data.get('name')
        email = data.get('email')
        role_id = int(data.get('role_id'))
        department_id = int(data.get('department_id'))
        status = data.get('status', 'Active')

        User.update_user(user_id, name, email, role_id, department_id, status)
        AuditLog.log(user['id'], 'UPDATE_USER', 'users', user_id, {'status': status, 'role_id': role_id})
        return jsonify({'success': True, 'message': 'User updated successfully.'})

@admin_bp.route('/users/<int:user_id>/reset-mfa', methods=['POST'])
def reset_mfa(user_id):
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    import pyotp
    new_secret = pyotp.random_base32()
    User.update_mfa_secret(user_id, new_secret, 1)
    AuditLog.log(user['id'], 'RESET_USER_MFA', 'users', user_id, {'new_secret': 'REDACTED'})
    return jsonify({'success': True, 'message': 'User MFA secret reset successfully.'})

@admin_bp.route('/policies', methods=['GET', 'PUT'])
def manage_policies():
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    if request.method == 'GET':
        policies = LeavePolicy.get_all()
        return jsonify({'success': True, 'policies': policies})
    elif request.method == 'PUT':
        data = request.json or {}
        policy_id = data.get('id')
        allowance = int(data.get('allowance', 12))
        max_days = int(data.get('max_consecutive_days', 5))
        active = 1 if data.get('active', True) else 0

        LeavePolicy.update(policy_id, allowance, max_days, active)
        AuditLog.log(user['id'], 'UPDATE_POLICY', 'leave_policies', policy_id, {'allowance': allowance, 'max_days': max_days})
        return jsonify({'success': True, 'message': 'Leave policy updated successfully.'})

@admin_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    logs = AuditLog.get_all(limit=200)
    return jsonify({'success': True, 'logs': logs})

@admin_bp.route('/audit-logs/export', methods=['GET'])
def export_audit_logs():
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    logs = AuditLog.get_all(limit=500)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Audit ID', 'Timestamp', 'User Name', 'Employee ID', 'Role', 'Action', 'Entity', 'Entity ID', 'Metadata', 'IP Address'])
    
    for l in logs:
        writer.writerow([
            l.get('id'),
            l.get('created_at'),
            l.get('user_name', 'System'),
            l.get('employee_id', 'N/A'),
            l.get('role_name', 'N/A'),
            l.get('action'),
            l.get('entity'),
            l.get('entity_id'),
            l.get('metadata'),
            l.get('ip_address')
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=SmartLeave_Audit_Logs.csv"}
    )
