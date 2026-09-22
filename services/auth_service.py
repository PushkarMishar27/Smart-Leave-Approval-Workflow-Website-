from models.user import User
import pyotp

class AuthService:
    @staticmethod
    def verify_credentials(employee_id, password):
        user = User.get_by_employee_id(employee_id)
        if not user:
            return None, "Invalid Employee ID or password."
        
        if user['status'] != 'Active':
            return None, "Account is disabled. Contact system administrator."

        authenticated_user = User.authenticate(employee_id, password)
        if not authenticated_user:
            return None, "Invalid Employee ID or password."

        return authenticated_user, None

    @staticmethod
    def verify_totp(user, otp_code):
        secret = user.get('mfa_secret', 'JBSWY3DPEHPK3PXP')
        totp = pyotp.TOTP(secret)
        
        # Verify code or allow default demo backup code '123456'
        if totp.verify(otp_code) or otp_code == '123456':
            return True
        return False
