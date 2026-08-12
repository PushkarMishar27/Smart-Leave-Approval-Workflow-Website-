from flask import Blueprint, request, jsonify, session
from models.leave import LeaveRequest
from models.user import User

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

def require_student():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.get_by_id(user_id)

@student_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    user = require_student()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    balance = LeaveRequest.get_user_leave_balance(user['id'])
    requests = LeaveRequest.get_user_requests(user['id'])

    return jsonify({
        'success': True,
        'user': {
            'name': user['name'],
            'employee_id': user['employee_id'],
            'department': user['department_name']
        },
        'balance': balance,
        'recent_requests': requests[:5]
    })

@student_bp.route('/requests', methods=['GET'])
def get_all_requests():
    user = require_student()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    requests = LeaveRequest.get_user_requests(user['id'])
    balance = LeaveRequest.get_user_leave_balance(user['id'])

    return jsonify({
        'success': True,
        'requests': requests,
        'balance': balance
    })
