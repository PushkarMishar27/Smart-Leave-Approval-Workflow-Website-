from models.leave import LeaveRequest, LeavePolicy
from models.approval import ApprovalStep
from models.user import User
from models.audit import AuditLog
from services.nlp_service import NLPClassifier
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService
import datetime

class LeaveService:
    @staticmethod
    def submit_leave(user_id, leave_type, start_date, end_date, reason):
        # Date Math calculation
        try:
            d1 = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            d2 = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            total_days = (d2 - d1).days + 1
        except Exception:
            return None, None, "Invalid date format. Use YYYY-MM-DD."

        if total_days <= 0:
            return None, None, "End date must be on or after start date."

        policy = LeavePolicy.get_by_type(leave_type)
        if policy and total_days > policy['max_consecutive_days']:
            return None, None, f"Exceeds maximum consecutive days allowed for {leave_type} ({policy['max_consecutive_days']} days)."

        # Balance check
        balances = LeaveService.calculate_user_balances(user_id)
        current_bal = balances.get(leave_type, {}).get('remaining', 12)
        if total_days > current_bal:
            return None, None, f"Insufficient balance for {leave_type}. Remaining: {current_bal} days, Requested: {total_days} days."

        # NLP classification
        ai_res = NLPClassifier.classify_reason(reason)
        ai_category = ai_res['category']
        ai_confidence = ai_res['confidence']

        # Determine level & escalation
        initial_level = WorkflowService.determine_initial_level(total_days, ai_category)

        # Create leave request
        req_id, req_num = LeaveRequest.create(
            user_id=user_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            ai_category=ai_category,
            ai_confidence=ai_confidence
        )

        # Update initial level if escalated directly to Admin
        if initial_level == 'Admin':
            LeaveRequest.update_status(req_id, 'Pending', 'Admin')

        # Log audit trail
        AuditLog.log(user_id, 'SUBMIT_LEAVE', 'leave_requests', req_id, {
            'request_number': req_num,
            'leave_type': leave_type,
            'days': total_days,
            'ai_category': ai_category
        })

        # Send Notifications
        user = User.get_by_id(user_id)
        NotificationService.send_notification(
            user_id=user_id,
            title=f"Application {req_num} Submitted",
            message=f"Your {leave_type} request for {total_days} day(s) has been submitted for approval."
        )

        return req_id, req_num, None

    @staticmethod
    def approve_leave(leave_id, approver_id, approver_role, comment):
        leave = LeaveRequest.get_by_id(leave_id)
        if not leave:
            return False, "Leave request not found."

        # Add approval step
        ApprovalStep.add_step(leave_id, approver_id, approver_role, 'Approved', comment)

        # Update Request Status to Approved
        LeaveRequest.update_status(leave_id, 'Approved', 'Completed')

        # Log audit trail
        AuditLog.log(approver_id, 'APPROVE_LEAVE', 'leave_requests', leave_id, {'status': 'Approved', 'comment': comment})

        # Notify student
        NotificationService.send_notification(
            user_id=leave['user_id'],
            title=f"Leave {leave['request_number']} Approved!",
            message=f"Your {leave['leave_type']} request for {leave['total_days']} day(s) was approved."
        )

        return True, f"Leave request {leave['request_number']} approved successfully."

    @staticmethod
    def reject_leave(leave_id, approver_id, approver_role, comment):
        leave = LeaveRequest.get_by_id(leave_id)
        if not leave:
            return False, "Leave request not found."

        ApprovalStep.add_step(leave_id, approver_id, approver_role, 'Rejected', comment)
        LeaveRequest.update_status(leave_id, 'Rejected', 'Completed')

        AuditLog.log(approver_id, 'REJECT_LEAVE', 'leave_requests', leave_id, {'status': 'Rejected', 'comment': comment})

        NotificationService.send_notification(
            user_id=leave['user_id'],
            title=f"Leave {leave['request_number']} Rejected",
            message=f"Your {leave['leave_type']} request was rejected. Reason: {comment}"
        )

        return True, f"Leave request {leave['request_number']} rejected."

    @staticmethod
    def forward_leave(leave_id, approver_id, comment):
        leave = LeaveRequest.get_by_id(leave_id)
        if not leave:
            return False, "Leave request not found."

        ApprovalStep.add_step(leave_id, approver_id, 'Faculty', 'Forwarded', comment)
        LeaveRequest.update_status(leave_id, 'Forwarded', 'Admin')

        AuditLog.log(approver_id, 'FORWARD_LEAVE', 'leave_requests', leave_id, {'comment': comment})

        NotificationService.send_notification(
            user_id=leave['user_id'],
            title=f"Leave {leave['request_number']} Forwarded",
            message=f"Your request has been forwarded to Admin for approval."
        )

        return True, f"Leave request {leave['request_number']} forwarded to Admin."

    @staticmethod
    def calculate_user_balances(user_id):
        policies = LeavePolicy.get_all()
        user_leaves = LeaveRequest.get_by_user_id(user_id)

        balances = {}
        for p in policies:
            lt = p['leave_type']
            allowance = p['allowance']
            used = sum(l['total_days'] for l in user_leaves if l['leave_type'] == lt and l['status'] == 'Approved')
            balances[lt] = {
                'allowance': allowance,
                'used': used,
                'remaining': max(0, allowance - used),
                'max_consecutive': p['max_consecutive_days']
            }
        return balances

    @staticmethod
    def get_approval_timeline(leave_id):
        return ApprovalStep.get_steps_for_request(leave_id)