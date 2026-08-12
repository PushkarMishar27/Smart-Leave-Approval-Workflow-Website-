from models.leave import LeaveRequest
from models.approval import ApprovalStep
from models.audit import AuditLog
from services.nlp_service import nlp_classifier
from services.workflow_service import WorkflowService
from services.notification_service import NotificationService
from models.user import User

class LeaveService:
    @staticmethod
    def submit_leave(user_id, leave_type, start_date, end_date, total_days, reason, document_path=None):
        # Run NLP classification
        nlp_res = nlp_classifier.classify_reason(reason)
        ai_category = nlp_res['category']
        ai_confidence = nlp_res['confidence']

        # Save leave request
        request_id, req_num = LeaveRequest.create(
            user_id=user_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            ai_category=ai_category,
            ai_confidence=ai_confidence,
            document_path=document_path
        )

        # Audit log
        AuditLog.log(user_id, 'SUBMIT_LEAVE', 'leave_requests', request_id, {
            'request_number': req_num,
            'leave_type': leave_type,
            'total_days': total_days,
            'ai_category': ai_category
        })

        # User notification
        user = User.get_by_id(user_id)
        NotificationService.create(
            user_id,
            'Leave Submitted',
            f'Your leave request #{req_num} for {total_days} day(s) has been submitted successfully.',
            'info'
        )

        # Notify department approver / faculty
        faculty_users = [u for u in User.get_all_users() if u['role_name'] == 'Faculty/Approver' and u['department_id'] == user['department_id']]
        for fac in faculty_users:
            NotificationService.create(
                fac['id'],
                'New Leave Review',
                f'New leave request #{req_num} from {user["name"]} requires your review.',
                'warning'
            )

        return request_id, req_num, nlp_res

    @staticmethod
    def process_approval_action(request_id, approver_id, action, comment=None):
        leave_req = LeaveRequest.get_by_id(request_id)
        if not leave_req:
            return False, 'Leave request not found.'

        approver = User.get_by_id(approver_id)
        if not approver:
            return False, 'Approver user invalid.'

        approver_level = 'Admin' if approver['role_name'] == 'Admin' else 'Faculty'
        
        # Evaluate workflow transition
        new_status, next_level = WorkflowService.evaluate_next_step(
            current_level=approver_level,
            action=action,
            total_days=leave_req['total_days'],
            ai_category=leave_req['ai_category']
        )

        # Update leave status
        LeaveRequest.update_status(request_id, new_status, next_level)

        # Record approval step
        ApprovalStep.add_step(request_id, approver_id, approver_level, action, comment)

        # Record audit log
        AuditLog.log(approver_id, f'{action.upper()}_LEAVE', 'leave_requests', request_id, {
            'request_number': leave_req['request_number'],
            'action': action,
            'new_status': new_status,
            'comment': comment
        })

        # Send notifications
        req_num = leave_req['request_number']
        applicant_id = leave_req['user_id']
        
        if new_status == 'Approved':
            NotificationService.create(
                applicant_id,
                'Leave Approved 🎉',
                f'Your leave request #{req_num} has been fully approved by {approver["name"]}. Balance updated.',
                'success'
            )
        elif new_status == 'Rejected':
            reason_msg = f' Reason: {comment}' if comment else ''
            NotificationService.create(
                applicant_id,
                'Leave Rejected',
                f'Your leave request #{req_num} was rejected by {approver["name"]}.{reason_msg}',
                'danger'
            )
        elif new_status == 'Forwarded':
            NotificationService.create(
                applicant_id,
                'Leave Escalated to Admin',
                f'Your leave request #{req_num} has been forwarded to Administration for secondary review.',
                'info'
            )
            # Notify admins
            admin_users = [u for u in User.get_all_users() if u['role_name'] == 'Admin']
            for adm in admin_users:
                NotificationService.create(
                    adm['id'],
                    'Escalated Approval Required',
                    f'Leave request #{req_num} from {leave_req["user_name"]} requires Admin approval.',
                    'warning'
                )

        return True, f'Leave request #{req_num} updated to {new_status}.'
