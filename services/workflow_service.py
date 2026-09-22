class WorkflowService:
    @staticmethod
    def determine_initial_level(total_days, ai_category):
        # Escalation rule: If leave duration > 3 days OR AI categorizes reason as Urgent -> Direct Admin review
        if total_days > 3 or ai_category == 'Urgent':
            return 'Admin'
        return 'Faculty'
