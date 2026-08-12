from flask import Blueprint, request, jsonify, session
from models.leave import LeaveRequest
from models.user import User

approver_bp = Blueprint('approver', __name__, url_prefix='/api/approver')

def require_approver():
    user_id = session.get('user_id')
    if not user_id:
        return None
    user = User.get_by_id(user_id)
    if not user or user['role_name'] not in ['Faculty/Approver', 'Admin']:
        return None
    return user

@approver_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    user = require_approver()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    pending = LeaveRequest.get_pending_for_approver(user['role_name'], user['department_id'])
    
    # Calculate approver statistics
    all_reqs = LeaveRequest.get_all_requests()
    approved_today = sum(1 for r in all_reqs if r['status'] == 'Approved')
    rejected_count = sum(1 for r in all_reqs if r['status'] == 'Rejected')
    forwarded_count = sum(1 for r in all_reqs if r['status'] == 'Forwarded')
    urgent_count = sum(1 for r in pending if r['ai_category'] == 'Urgent')

    return jsonify({
        'success': True,
        'user': {
            'name': user['name'],
            'employee_id': user['employee_id'],
            'role': user['role_name'],
            'department': user['department_name']
        },
        'stats': {
            'pending_count': len(pending),
            'approved_today': approved_today,
            'rejected_count': rejected_count,
            'forwarded_count': forwarded_count,
            'urgent_count': urgent_count
        },
        'pending_requests': pending
    })
