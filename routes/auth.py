from flask import Blueprint, request, jsonify, session, redirect, url_for
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
        session.pop('temp_user_id', None)
        session['user_id'] = user['id']
        session['employee_id'] = user['employee_id']
        session['user_name'] = user['name']
        session['role_name'] = user['role_name']
        session['department_id'] = user['department_id']
        
        User.update_last_login(user['id'])

        redirect_url = '/student/dashboard'
        if user['role_name'] == 'Faculty/Approver':
            redirect_url = '/approver/dashboard'
        elif user['role_name'] == 'Admin':
            redirect_url = '/admin/dashboard'

        return jsonify({
            'success': True,
            'message': 'Login successful.',
            'redirect_url': redirect_url
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid TOTP code.'}), 401

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    if request.method == 'GET':
        return redirect('/login')
    return jsonify({'success': True, 'message': 'Logged out successfully.', 'redirect_url': '/login'})