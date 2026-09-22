from flask import Blueprint, request, jsonify, session
from services.leave_service import LeaveService
from services.nlp_service import NLPClassifier
from models.leave import LeaveRequest
from models.user import User

leaves_bp = Blueprint('leaves', __name__, url_prefix='/api/leaves')

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.get_by_id(user_id)

@leaves_bp.route('', methods=['POST'])
def submit_leave():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.json or {}
    leave_type = data.get('leave_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    reason = data.get('reason', '').strip()

    if not leave_type or not start_date or not end_date or not reason:
        return jsonify({'success': False, 'message': 'Please fill all required fields.'}), 400

    req_id, req_num, err = LeaveService.submit_leave(
        user_id=user['id'],
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason
    )

    if err:
        return jsonify({'success': False, 'message': err}), 400

    return jsonify({
        'success': True,
        'message': f'Leave application {req_num} submitted successfully.',
        'request_id': req_id,
        'request_number': req_num
    })

@leaves_bp.route('/classify-reason', methods=['POST'])
def classify_reason():
    data = request.json or {}
    reason = data.get('reason', '')

    res = NLPClassifier.classify_reason(reason)
    return jsonify({
        'success': True,
        'ai_category': res['category'],
        'confidence': res['confidence'],
        'reason_snippet': reason[:50]
    })

@leaves_bp.route('/<int:leave_id>', methods=['GET'])
def get_leave_detail(leave_id):
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    leave = LeaveRequest.get_by_id(leave_id)
    if not leave:
        return jsonify({'success': False, 'message': 'Leave request not found.'}), 404

    # Verification: Student can only view their own leave, Approvers/Admin can view all
    if user['role_name'] == 'Student/Employee' and leave['user_id'] != user['id']:
        return jsonify({'success': False, 'message': 'Access denied.'}), 403

    steps = LeaveService.get_approval_timeline(leave_id)
    return jsonify({
        'success': True,
        'leave': leave,
        'timeline': steps
    })

@leaves_bp.route('/<int:leave_id>/approve', methods=['POST'])
def approve_leave(leave_id):
    user = get_current_user()
    if not user or user['role_name'] not in ['Faculty/Approver', 'Admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.json or {}
    comment = data.get('comment', 'Approved')

    success, msg = LeaveService.approve_leave(leave_id, user['id'], user['role_name'], comment)
    if not success:
        return jsonify({'success': False, 'message': msg}), 400

    return jsonify({'success': True, 'message': msg})

@leaves_bp.route('/<int:leave_id>/reject', methods=['POST'])
def reject_leave(leave_id):
    user = get_current_user()
    if not user or user['role_name'] not in ['Faculty/Approver', 'Admin']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.json or {}
    comment = data.get('comment', '').strip()

    if not comment:
        return jsonify({'success': False, 'message': 'Please provide a reason for rejection.'}), 400

    success, msg = LeaveService.reject_leave(leave_id, user['id'], user['role_name'], comment)
    if not success:
        return jsonify({'success': False, 'message': msg}), 400

    return jsonify({'success': True, 'message': msg})

@leaves_bp.route('/<int:leave_id>/forward', methods=['POST'])
def forward_leave(leave_id):
    user = get_current_user()
    if not user or user['role_name'] != 'Faculty/Approver':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    data = request.json or {}
    comment = data.get('comment', 'Forwarded to Admin')

    success, msg = LeaveService.forward_leave(leave_id, user['id'], comment)
    if not success:
        return jsonify({'success': False, 'message': msg}), 400

    return jsonify({'success': True, 'message': msg})