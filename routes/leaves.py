from flask import Blueprint, request, jsonify, session
from services.leave_service import LeaveService
from services.nlp_service import nlp_classifier
from models.leave import LeaveRequest
from models.approval import ApprovalStep
from models.user import User

leaves_bp = Blueprint('leaves', __name__, url_prefix='/api/leaves')

@leaves_bp.route('/classify-reason', methods=['POST'])
def classify_reason():
    data = request.json or {}
    reason = data.get('reason', '')
    res = nlp_classifier.classify_reason(reason)
    return jsonify({'success': True, 'classification': res})

@leaves_bp.route('', methods=['POST'])
def submit_leave():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.json or {}
    leave_type = data.get('leave_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    total_days = int(data.get('total_days', 1))
    reason = data.get('reason', '').strip()
    document_path = data.get('document_path')

    if not leave_type or not start_date or not end_date or not reason:
        return jsonify({'success': False, 'message': 'Please fill all required fields.'}), 400

    req_id, req_num, nlp_res = LeaveService.submit_leave(
        user_id=user_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        reason=reason,
        document_path=document_path
    )

    return jsonify({
        'success': True,
        'message': f'Leave request #{req_num} submitted successfully.',
        'request_id': req_id,
        'request_number': req_num,
        'ai_classification': nlp_res
    })

@leaves_bp.route('/<int:request_id>', methods=['GET'])
def get_leave_detail(request_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    leave = LeaveRequest.get_by_id(request_id)
    if not leave:
        return jsonify({'success': False, 'message': 'Leave request not found.'}), 404

    # RBAC check: allow user if owner, approver, or admin
    user = User.get_by_id(user_id)
    if user['role_name'] == 'Student/Employee' and leave['user_id'] != user_id:
        return jsonify({'success': False, 'message': 'Access denied.'}), 403

    steps = ApprovalStep.get_steps_for_request(request_id)
    user_balance = LeaveRequest.get_user_leave_balance(leave['user_id'])

    return jsonify({
        'success': True,
        'leave': leave,
        'approval_timeline': steps,
        'user_balance': user_balance
    })

@leaves_bp.route('/<int:request_id>/approve', methods=['POST'])
def approve_leave(request_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.json or {}
    comment = data.get('comment', 'Approved')

    ok, msg = LeaveService.process_approval_action(request_id, user_id, 'Approve', comment)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@leaves_bp.route('/<int:request_id>/reject', methods=['POST'])
def reject_leave(request_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.json or {}
    comment = data.get('comment', '').strip()
    if not comment:
        return jsonify({'success': False, 'message': 'Rejection reason is required.'}), 400

    ok, msg = LeaveService.process_approval_action(request_id, user_id, 'Reject', comment)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400

@leaves_bp.route('/<int:request_id>/forward', methods=['POST'])
def forward_leave(request_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Authentication required.'}), 401

    data = request.json or {}
    comment = data.get('comment', 'Forwarded to Administration for secondary approval.')

    ok, msg = LeaveService.process_approval_action(request_id, user_id, 'Forward', comment)
    if ok:
        return jsonify({'success': True, 'message': msg})
    return jsonify({'success': False, 'message': msg}), 400
