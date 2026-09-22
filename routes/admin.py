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
    audit_logs = AuditLog.get_all(50)

    dept_counts = {}
    for u in users:
        dept = u['department_name']
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    pending_leaves = sum(1 for l in all_leaves if l['status'] == 'Pending')
    approved_leaves = sum(1 for l in all_leaves if l['status'] == 'Approved')
    rejected_leaves = sum(1 for l in all_leaves if l['status'] == 'Rejected')

    return jsonify({
        'success': True,
        'user': {
            'name': user['name'],
            'employee_id': user['employee_id'],
            'role': user['role_name']
        },
        'stats': {
            'total_users': len(users),
            'total_requests': len(all_leaves),
            'pending_requests': pending_leaves,
            'approved_requests': approved_leaves,
            'rejected_requests': rejected_leaves,
            'status_breakdown': {
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

@admin_bp.route('/users/<int:target_user_id>', methods=['DELETE'])
def delete_user_route(target_user_id):
    current_admin = require_admin()
    if not current_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    if current_admin['id'] == target_user_id:
        return jsonify({'success': False, 'message': 'Cannot delete your own admin account while logged in.'}), 400

    target = User.get_by_id(target_user_id)
    if not target:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    User.delete_user(target_user_id)
    AuditLog.log(current_admin['id'], 'DELETE_USER', 'users', target_user_id, {
        'employee_id': target.get('employee_id'),
        'name': target.get('name')
    })
    return jsonify({'success': True, 'message': f"User '{target['name']}' ({target['employee_id']}) has been deleted."})

@admin_bp.route('/faculty-assignments', methods=['GET'])
def get_faculty_assignments():
    current_admin = require_admin()
    if not current_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    faculty_list = User.get_faculty_members()
    student_list = User.get_students()

    return jsonify({
        'success': True,
        'faculty_members': faculty_list,
        'students': student_list
    })

@admin_bp.route('/assign-faculty', methods=['POST'])
def assign_faculty():
    current_admin = require_admin()
    if not current_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.json or {}
    faculty_id = int(data.get('faculty_id', 0))
    student_ids = data.get('student_ids', [])

    if not faculty_id:
        return jsonify({'success': False, 'message': 'Please select a Faculty member.'}), 400

    if not student_ids or not isinstance(student_ids, list):
        return jsonify({'success': False, 'message': 'Please select at least one student.'}), 400

    faculty = User.get_by_id(faculty_id)
    if not faculty:
        return jsonify({'success': False, 'message': 'Selected faculty member not found.'}), 404

    User.assign_faculty_to_students(faculty_id, student_ids)
    
    AuditLog.log(current_admin['id'], 'ASSIGN_FACULTY', 'users', faculty_id, {
        'faculty_name': faculty['name'],
        'student_ids': student_ids,
        'assigned_count': len(student_ids)
    })

    return jsonify({
        'success': True,
        'message': f"Successfully assigned {faculty['name']} to {len(student_ids)} student(s)."
    })

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
        max_days = int(data.get('max_consecutive_days', 3))

        LeavePolicy.update_policy(policy_id, allowance, max_days)
        AuditLog.log(user['id'], 'UPDATE_POLICY', 'leave_policies', policy_id, {'allowance': allowance, 'max_days': max_days})
        return jsonify({'success': True, 'message': 'Policy updated successfully.'})

@admin_bp.route('/audit', methods=['GET'])
def get_audit_logs():
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    logs = AuditLog.get_all(100)
    return jsonify({'success': True, 'audit_logs': logs})

@admin_bp.route('/audit/export', methods=['GET'])
def export_audit_csv():
    user = require_admin()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    logs = AuditLog.get_all(500)
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Log ID', 'Timestamp', 'User', 'Employee ID', 'Role', 'Action', 'Target Entity', 'Target ID', 'IP Address', 'Details'])
    for l in logs:
        writer.writerow([
            l.get('id'),
            l.get('timestamp'),
            l.get('user_name', 'System'),
            l.get('employee_id', 'N/A'),
            l.get('role_name', 'N/A'),
            l.get('action'),
            l.get('target_entity'),
            l.get('target_id'),
            l.get('ip_address'),
            l.get('details')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=SmartLeave_Audit_Logs.csv'}
    )