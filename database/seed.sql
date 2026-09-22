-- SmartLeave Indian Institution Seed Data Script

USE smartleave_db;

-- 1. Departments (Indian Context)
INSERT IGNORE INTO departments (id, name, code) VALUES
(1, 'Computer Science & Eng.', 'CSE'),
(2, 'Information Technology', 'IT'),
(3, 'Electronics & Comm.', 'ECE'),
(4, 'Electrical Engineering', 'EE'),
(5, 'Mechanical Engineering', 'ME'),
(6, 'Administration', 'ADMIN');

-- 2. Roles
INSERT IGNORE INTO roles (id, name, description) VALUES
(1, 'Student/Employee', 'Can submit leave applications and track leave status/balances.'),
(2, 'Faculty/Approver', 'Can review, approve, reject, or forward assigned leave applications.'),
(3, 'Admin', 'Full administrative control over users, policies, workflows, and audit logs.');

-- 3. Permissions
INSERT IGNORE INTO permissions (id, name, description) VALUES
(1, 'apply_leave', 'Submit new leave requests'),
(2, 'view_own_requests', 'View personal leave requests & balance'),
(3, 'review_assigned_leaves', 'Approve, reject, or forward pending assigned leaves'),
(4, 'manage_users', 'Add, edit, or disable user accounts'),
(5, 'manage_policies', 'Modify leave allowances and threshold rules'),
(6, 'view_audit_logs', 'View and export system audit trail logs');

-- 4. Map Role Permissions
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
(1, 1), (1, 2),
(2, 3), (2, 2),
(3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6);

-- 5. Insert Indian Users (Default password for all accounts: 'password123')
INSERT IGNORE INTO users (id, employee_id, name, email, password_hash, role_id, department_id, mfa_secret, mfa_enabled, status) VALUES
(1, 'STU1001', 'Aarav Sharma', 'aarav.sharma@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 1, 1, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
(2, 'STU1002', 'Ananya Iyer', 'ananya.iyer@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 1, 1, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
(3, 'STU1003', 'Rohan Verma', 'rohan.verma@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 1, 2, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
(4, 'STU1004', 'Priya Patel', 'priya.patel@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 1, 3, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
(5, 'STU1005', 'Vikram Singh', 'vikram.singh@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 1, 4, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
(6, 'FAC2001', 'Dr. Rajesh Kumar', 'rajesh.kumar@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 2, 1, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
(7, 'FAC2002', 'Prof. Sunita Rao', 'sunita.rao@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 2, 2, 'JBSWY3DPEHPK3PXP', 1, 'Active'),
(8, 'ADM3001', 'Pushkar Mishra', 'pushkar.mishra@smartleave.edu.in', 'scrypt:32768:8:1$u7xK7O6yW1k3m2a7$8e945c2cf72a5a587dd439063c4379a0cf5fbfaedfa0c62bd93ec974e64f7df56c3ee796d194c502b4d18fae47571db29c8e19e7552554743ceb6c317fdbfbfb', 3, 6, 'JBSWY3DPEHPK3PXP', 1, 'Active');

-- 6. Leave Policies
INSERT IGNORE INTO leave_policies (id, leave_type, allowance, max_consecutive_days, department_id, active) VALUES
(1, 'Casual Leave', 12, 3, 1, 1),
(2, 'Medical Leave', 10, 7, 1, 1),
(3, 'Personal Leave', 8, 4, 1, 1),
(4, 'Emergency Leave', 5, 2, 1, 1);

-- 7. Realistic Indian Leave Requests
INSERT IGNORE INTO leave_requests (id, request_number, user_id, leave_type, start_date, end_date, total_days, reason, ai_category, ai_confidence, status, current_level) VALUES
(101, 'LV-2026-001', 1, 'Medical Leave', '2026-08-12', '2026-08-14', 3, 'High dengue fever and doctor recommended complete bed rest for 3 days at Apollo Hospital.', 'Medical', 96.4, 'Pending', 'Faculty'),
(102, 'LV-2026-002', 1, 'Casual Leave', '2026-07-10', '2026-07-11', 2, 'Attending cousin wedding ceremony in Jaipur, Rajasthan.', 'Personal', 91.2, 'Approved', 'Faculty'),
(103, 'LV-2026-003', 2, 'Emergency Leave', '2026-08-15', '2026-08-18', 4, 'Family medical emergency requiring immediate travel to Chennai.', 'Urgent', 94.8, 'Forwarded', 'Admin'),
(104, 'LV-2026-004', 3, 'Personal Leave', '2026-09-01', '2026-09-03', 3, 'Attending Smart India Hackathon final round at IIT Bombay.', 'Personal', 88.5, 'Pending', 'Faculty');

-- 8. Approval Steps
INSERT IGNORE INTO approval_steps (id, leave_request_id, approver_id, level, status, comment, action_at) VALUES
(1, 102, 6, 'Faculty', 'Approved', 'Approved as requested. Enjoy the wedding.', '2026-07-09 10:30:00'),
(2, 103, 6, 'Faculty', 'Forwarded', 'Forwarding to Registrar Admin since duration exceeds 3 days.', '2026-08-10 08:15:00');

-- 9. Notifications
INSERT IGNORE INTO notifications (id, user_id, title, message, type, read_status) VALUES
(1, 1, 'Leave Request Approved', 'Your leave request #LV-2026-002 has been approved by Dr. Rajesh Kumar.', 'success', 1),
(2, 1, 'Leave Under Review', 'Your leave request #LV-2026-001 is awaiting review by Dr. Rajesh Kumar.', 'info', 0),
(3, 6, 'Approval Required', 'New leave request #LV-2026-001 from Aarav Sharma requires your review.', 'warning', 0);

-- 10. Audit Logs
INSERT IGNORE INTO audit_logs (id, user_id, action, entity, entity_id, metadata) VALUES
(1, 1, 'USER_LOGIN', 'users', 1, '{"method": "TOTP_MFA", "status": "Success"}'),
(2, 1, 'SUBMIT_LEAVE', 'leave_requests', 101, '{"type": "Medical Leave", "days": 3}'),
(3, 6, 'APPROVE_LEAVE', 'leave_requests', 102, '{"approver": "Dr. Rajesh Kumar", "level": "Faculty"}');
