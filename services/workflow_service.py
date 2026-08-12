class WorkflowService:
    THRESHOLD_DAYS = 3  # Leaves > 3 days require Admin secondary approval

    @classmethod
    def determine_initial_level(cls, total_days, ai_category):
        """
        Determines the starting approver level based on duration and NLP urgency.
        """
        if total_days > cls.THRESHOLD_DAYS or ai_category == 'Urgent':
            # Highlighted for mandatory Admin review after Faculty, or initial routing
            return 'Faculty'
        return 'Faculty'

    @classmethod
    def evaluate_next_step(cls, current_level, action, total_days, ai_category):
        """
        Evaluates the next state after an action (Approve/Forward/Reject).
        """
        if action == 'Reject':
            return 'Rejected', 'Completed'

        if action == 'Forward':
            return 'Forwarded', 'Admin'

        if action == 'Approve':
            if current_level == 'Faculty':
                if total_days > cls.THRESHOLD_DAYS or ai_category == 'Urgent':
                    # Needs Admin review
                    return 'Forwarded', 'Admin'
                else:
                    return 'Approved', 'Completed'
            elif current_level == 'Admin':
                return 'Approved', 'Completed'

        return 'Pending', current_level
