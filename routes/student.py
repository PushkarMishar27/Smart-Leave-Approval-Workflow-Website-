from flask import Blueprint, request, jsonify, session
from models.leave import LeaveRequest, LeavePolicy
from models.user import User
from services.leave_service import LeaveService

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

def require_student():
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = User.get_by_id(user_id)
    if not user:
        return None
    return user

@student_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    user = require_student()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    leaves = LeaveRequest.get_by_user_id(user['id'])
    policies = LeavePolicy.get_all()
    balances = LeaveService.calculate_user_balances(user['id'])

    return jsonify({
        'success': True,
        'user': {
            'name': user['name'],
            'employee_id': user['employee_id'],
            'role': user['role_name'],
            'department': user['department_name'],
            'advisor_name': user.get('advisor_name')
        },
        'balances': balances,
        'leaves': leaves[:10],
        'stats': {
            'total_applied': len(leaves),
            'pending_count': sum(1 for l in leaves if l['status'] == 'Pending'),
            'approved_count': sum(1 for l in leaves if l['status'] == 'Approved'),
            'rejected_count': sum(1 for l in leaves if l['status'] == 'Rejected')
        }
    })

@student_bp.route('/leaves', methods=['GET'])
def get_student_leaves():
    user = require_student()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    leaves = LeaveRequest.get_by_user_id(user['id'])
    return jsonify({'success': True, 'leaves': leaves})
