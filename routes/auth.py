from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    employee_id = data.get('employee_id', '').strip()
    password = data.get('password', '')
    
    if not employee_id or not password:
        return jsonify({'success': False, 'message': 'Please provide Employee ID and password.'}), 400

    user, err = AuthService.verify_credentials(employee_id, password)
    if err:
        return jsonify({'success': False, 'message': err}), 401

    # Stage 1 successful: prompt for MFA
    session['temp_user_id'] = user['id']
    return jsonify({
        'success': True,
        'requires_mfa': True,
        'user_name': user['name'],
        'employee_id': user['employee_id'],
        'role': user['role_name'],
        'message': 'Credentials verified. Please enter your 6-digit MFA verification code.'
    })

@auth_bp.route('/verify-mfa', methods=['POST'])
def verify_mfa():
    temp_user_id = session.get('temp_user_id')
    data = request.json or {}
    otp_code = data.get('otp_code', '').strip()

    if not temp_user_id:
        return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401

    if not otp_code or len(otp_code) != 6:
        return jsonify({'success': False, 'message': 'Please enter a valid 6-digit MFA code.'}), 400

    user = User.get_by_id(temp_user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    if AuthService.verify_totp(user, otp_code):
        # MFA Success -> Bind Session
        session.pop('temp_user_id', None)
        session['user_id'] = user['id']
        session['employee_id'] = user['employee_id']
        session['user_name'] = user['name']
        session['role_name'] = user['role_name']
        session['department_id'] = user['department_id']

        # Determine redirect route based on RBAC
        role = user['role_name']
        if role == 'Admin':
            redirect_url = '/admin/dashboard'
        elif role == 'Faculty/Approver':
            redirect_url = '/approver/dashboard'
        else:
            redirect_url = '/student/dashboard'

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'employee_id': user['employee_id'],
                'role': user['role_name'],
                'department': user['department_name']
            },
            'redirect_url': redirect_url
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid authentication code. Please try again.'}), 400

from flask import redirect

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': 'Logged out successfully.', 'redirect_url': '/login'})
    return redirect('/login')

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 401
    user = User.get_by_id(user_id)
    if not user:
        session.clear()
        return jsonify({'authenticated': False}), 401
    return jsonify({'authenticated': True, 'user': user})
