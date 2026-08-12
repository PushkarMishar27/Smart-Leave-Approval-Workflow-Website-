from flask import Flask, render_template, redirect, url_for, session, request, jsonify
from config import Config
from models.database import init_db
from models.user import User
from models.leave import LeaveRequest, LeavePolicy
from models.approval import ApprovalStep
from models.audit import AuditLog

# Import API blueprints
from routes.auth import auth_bp
from routes.student import student_bp
from routes.approver import approver_bp
from routes.admin import admin_bp
from routes.leaves import leaves_bp
from routes.notifications import notifications_bp

app = Flask(__name__)
app.config.from_object(Config)

# Register API Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(approver_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(leaves_bp)
app.register_blueprint(notifications_bp)

# Initialize database schema & seed data
init_db()

# --- Page Rendering Routes ---

@app.route('/')
def landing_page():
    return render_template('index.html')

@app.route('/login')
def login_page():
    if session.get('user_id'):
        role = session.get('role_name')
        if role == 'Admin':
            return redirect(url_for('admin_dashboard_page'))
        elif role == 'Faculty/Approver':
            return redirect(url_for('approver_dashboard_page'))
        else:
            return redirect(url_for('student_dashboard_page'))
    return render_template('login.html')

# Student Routes
@app.route('/student/dashboard')
def student_dashboard_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user:
        return redirect(url_for('login_page'))
    
    balance = LeaveRequest.get_user_leave_balance(user_id)
    recent = LeaveRequest.get_user_requests(user_id)
    return render_template('student_dashboard.html', user=user, balance=balance, recent_requests=recent[:5])

@app.route('/student/apply')
def student_apply_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    return render_template('apply_leave.html', user=user)

@app.route('/student/requests')
def student_requests_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    balance = LeaveRequest.get_user_leave_balance(user_id)
    recent = LeaveRequest.get_user_requests(user_id)
    return render_template('student_dashboard.html', user=user, balance=balance, recent_requests=recent)

@app.route('/request/<int:request_id>')
def request_detail_page(request_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    leave = LeaveRequest.get_by_id(request_id)
    if not leave:
        return render_template('error.html', error_code='404', title='Request Not Found', message='Leave request does not exist.'), 404
    steps = ApprovalStep.get_steps_for_request(request_id)
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

    pending = LeaveRequest.get_pending_for_approver(user['role_name'], user['department_id'])
    all_reqs = LeaveRequest.get_all_requests()
    approved_today = sum(1 for r in all_reqs if r['status'] == 'Approved')
    rejected_count = sum(1 for r in all_reqs if r['status'] == 'Rejected')
    forwarded_count = sum(1 for r in all_reqs if r['status'] == 'Forwarded')
    urgent_count = sum(1 for r in pending if r['ai_category'] == 'Urgent')

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
    audit_logs = AuditLog.get_all(limit=50)

    category_counts = {'Medical': 0, 'Personal': 0, 'Urgent': 0}
    for l in all_leaves:
        cat = l.get('ai_category', 'Personal')
        category_counts[cat] = category_counts.get(cat, 0) + 1

    dept_counts = {}
    for l in all_leaves:
        dept = l.get('department_name', 'General')
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    stats = {
        'total_users': len(users),
        'active_users': sum(1 for u in users if u['status'] == 'Active'),
        'pending_leaves': sum(1 for l in all_leaves if l['status'] in ('Pending', 'Forwarded')),
        'approved_leaves': sum(1 for l in all_leaves if l['status'] == 'Approved'),
        'rejected_leaves': sum(1 for l in all_leaves if l['status'] == 'Rejected'),
        'audit_events_count': len(audit_logs)
    }

    charts = {
        'categories': category_counts,
        'status': {
            'Pending': stats['pending_leaves'],
            'Approved': stats['approved_leaves'],
            'Rejected': stats['rejected_leaves']
        },
        'departments': dept_counts
    }

    return render_template('admin_dashboard.html', user=user, stats=stats, charts=charts, recent_audit=audit_logs[:10])

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
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return render_template('error.html', error_code='403', title='Access Denied', message='Administrator rights required.'), 403
    return render_template('admin_roles.html', user=user)

@app.route('/admin/workflow')
def admin_workflow_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return render_template('error.html', error_code='403', title='Access Denied', message='Administrator rights required.'), 403
    return render_template('admin_workflow.html', user=user)

@app.route('/admin/policies')
def admin_policies_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return render_template('error.html', error_code='403', title='Access Denied', message='Administrator rights required.'), 403
    policies = LeavePolicy.get_all()
    return render_template('admin_policies.html', user=user, policies=policies)

@app.route('/admin/audit')
def admin_audit_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return render_template('error.html', error_code='403', title='Access Denied', message='Administrator rights required.'), 403
    audit_logs = AuditLog.get_all(limit=100)
    return render_template('admin_audit.html', user=user, audit_logs=audit_logs)

@app.route('/admin/reports')
def admin_reports_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    if not user or user['role_name'] != 'Admin':
        return render_template('error.html', error_code='403', title='Access Denied', message='Administrator rights required.'), 403
    return render_template('admin_reports.html', user=user)

@app.route('/logout')
def logout_shortcut():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/profile')
def profile_page():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))
    user = User.get_by_id(user_id)
    return render_template('error.html', error_code='Profile', title=f'{user["name"]} Profile Settings', message=f'Employee ID: {user["employee_id"]} | Role: {user["role_name"]} | Department: {user["department_name"]} | TOTP MFA: Active')

# Custom Error Handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code='403', title='Access Denied', message='You do not have permission to access this page.'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code='404', title='Page Not Found', message='The requested page does not exist.'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error_code='500', title='Internal Server Error', message='An unexpected server error occurred.'), 500

if __name__ == '__main__':
    print("==========================================================")
    print("Starting SmartLeave Web Server at http://127.0.0.1:5000")
    print("==========================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
