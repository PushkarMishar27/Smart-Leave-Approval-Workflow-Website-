import pyotp
from models.user import User
from models.audit import AuditLog

class AuthService:
    @staticmethod
    def verify_credentials(employee_id, password):
        user = User.authenticate(employee_id, password)
        if user:
            if user['status'] != 'Active':
                return None, 'Account is disabled. Contact Administrator.'
            return user, None
        return None, 'Invalid Employee/Staff ID or password.'

    @staticmethod
    def verify_totp(user, otp_code):
        secret = user.get('mfa_secret') or 'JBSWY3DPEHPK3PXP'
        totp = pyotp.TOTP(secret)
        
        # Development / Demo bypass code: 123456
        if otp_code == '123456' or totp.verify(otp_code, valid_window=2):
            User.update_last_login(user['id'])
            AuditLog.log(user['id'], 'LOGIN_SUCCESS', 'users', user['id'], {'method': 'TOTP_MFA'})
            return True
        return False

    @staticmethod
    def generate_mfa_setup(email):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=email, issuer_name="SmartLeave")
        return secret, provisioning_uri
