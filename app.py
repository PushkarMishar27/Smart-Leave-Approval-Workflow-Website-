from flask import Flask, render_template, redirect, url_for, session
from config import Config
from models.database import init_db
from models.user import User
from models.leave import LeaveRequest
from services.leave_service import LeaveService
from services.notification_service import NotificationService

# Import API Blueprints
from routes.auth import auth_bp
from routes.student import student_bp
from routes.approver import approver_bp
from routes.admin import admin_bp
from routes.leaves import leaves_bp
from routes.notifications import notifications_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Database Schema & Seed Data
init_db()

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(approver_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(leaves_bp)
app.register_blueprint(notifications_bp)

# Page Controllers
@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/login')
def login_page():
    if session.get('user_id'):
        role = session.get('role_name')
        if role == 'Student/Employee':
            return redirect(url_for('student_dashboard_page'))
        elif role == 'Faculty/Approver':
            return redirect(url_for('approver_dashboard_page'))
        elif role == 'Admin':
            return redirect(url_for('admin_dashboard_page'))
    return render_template('login.html')

@app.route('/logout')
def logout_redirect():
    session.clear()
    return redirect(url_for('login_page'))

# Student Routes
@app.route('/student/dashboard')
def student_dashboard_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user:
        return redirect(url_for('login_page'))

    leaves = LeaveRequest.get_by_user_id(user_id)
    balances = LeaveService.calculate_user_balances(user_id)
    notifs = NotificationService.get_user_notifications(user_id)
    unread_count = sum(1 for n in notifs if not n.get('is_read'))

    return render_template(
        'student_dashboard.html',
        user=user,
        leaves=leaves,
        balances=balances,
        unread_count=unread_count
    )

@app.route('/student/apply')
def apply_leave_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    balances = LeaveService.calculate_user_balances(user_id)
    return render_template('apply_leave.html', user=user, balances=balances)

@app.route('/request/<int:request_id>')
def request_detail_page(request_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    
    leave = LeaveRequest.get_by_id(request_id)
    if not leave:
        return render_template('error.html', error_code='404', title='Not Found', message='Leave request not found.'), 404

    steps = LeaveService.get_approval_timeline(request_id)
    return render_template('request_detail.html', leave=leave, approval_timeline=steps)

# Approver Routes
@app.route('/approver/dashboard')
def approver_dashboard_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] not in ['Faculty/Approver', 'Admin']:
        return render_template('error.html', error_code='403', title='Access Denied', message='Approver authorization required.'), 403

    pending = LeaveRequest.get_pending_for_approver(user['role_name'], user['department_id'], user['id'])
    all_reqs = LeaveRequest.get_all_requests()
    approved_today = sum(1 for r in all_reqs if r['status'] == 'Approved')
    rejected_count = sum(1 for r in all_reqs if r['status'] == 'Rejected')
    forwarded_count = sum(1 for r in all_reqs if r['status'] == 'Forwarded')
    urgent_count = sum(1 for r in pending if r.get('ai_category') == 'Urgent')

    stats = {
        'pending_count': len(pending),
        'approved_today': approved_today,
        'rejected_count': rejected_count,
        'forwarded_count': forwarded_count,
        'urgent_count': urgent_count
    }

    return render_template('approver_dashboard.html', user=user, pending_requests=pending, stats=stats)

# Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return render_template('error.html', error_code='403', title='Access Denied', message='Administrator rights required.'), 403

    users = User.get_all_users()
    all_leaves = LeaveRequest.get_all_requests()

    stats = {
        'total_users': len(users),
        'total_requests': len(all_leaves),
        'pending_requests': sum(1 for l in all_leaves if l['status'] == 'Pending'),
        'approved_requests': sum(1 for l in all_leaves if l['status'] == 'Approved'),
        'rejected_requests': sum(1 for l in all_leaves if l['status'] == 'Rejected')
    }

    return render_template('admin_dashboard.html', user=user, stats=stats, recent_leaves=all_leaves[:10])

@app.route('/admin/users')
def admin_users_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return render_template('error.html', error_code='403', title='Access Denied', message='Administrator rights required.'), 403

    users = User.get_all_users()
    return render_template('admin_users.html', user=user, users=users)

@app.route('/admin/roles')
def admin_roles_page():
    return render_template('admin_roles.html')

@app.route('/admin/workflow')
def admin_workflow_page():
    return render_template('admin_workflow.html')

@app.route('/admin/policies')
def admin_policies_page():
    return render_template('admin_policies.html')

@app.route('/admin/audit')
def admin_audit_page():
    return render_template('admin_audit.html')

@app.route('/admin/reports')
def admin_reports_page():
    return render_template('admin_reports.html')

# Custom Error Handlers
@app.errorhandler(403)
def access_denied(e):
    return render_template('error.html', error_code='403', title='Access Denied', message='You do not have permission to view this resource.'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code='404', title='Page Not Found', message='The requested page could not be found.'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error_code='500', title='Internal Server Error', message='An unexpected server error occurred.'), 500

if __name__ == '__main__':
    print("==========================================================")
    print("Starting SmartLeave Web Server at http://127.0.0.1:5000")
    print("==========================================================")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
