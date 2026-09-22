# SmartLeave — Smart Leave Approval Workflow System

> **“Leave management, intelligently simplified.”**

SmartLeave is a digital leave-management platform for **Students/Employees**, **Faculty/Approvers**, and **Administrators**. It features AI reason classification (`scikit-learn`), TOTP MFA (`pyotp`), role-based access control (RBAC), real-time notifications, dark mode, and an immutable audit log.

---

## 📁 Project Structure

```text
smartleave/
├── app.py                      # Flask Application entry point & route controllers
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies (Flask, PyOTP, scikit-learn, etc.)
├── smartleave.db               # Pre-populated SQLite Database (auto-generated)
│
├── models/
│   ├── database.py             # Database connector (SQLite fallback / MySQL support)
│   ├── user.py                 # User & RBAC schema models
│   ├── leave.py                # Leave request & Policy models
│   ├── approval.py             # Multi-level approval steps models
│   └── audit.py                # Audit log models
│
├── services/
│   ├── auth_service.py         # Password hashing & TOTP MFA validation
│   ├── leave_service.py        # Leave submission & approval processing
│   ├── workflow_service.py     # Escalation rules engine (>3 days / Urgent -> Admin)
│   ├── nlp_service.py          # scikit-learn TF-IDF reason classifier
│   ├── notification_service.py # System notifications manager
│   └── audit_service.py        # Audit logging service
│
├── routes/
│   ├── auth.py                 # Login, MFA, Logout API routes
│   ├── student.py              # Student portal API routes
│   ├── approver.py             # Faculty review queue API routes
│   ├── admin.py                # Admin management API routes (Users, Delete, Assign Faculty, CSV)
│   ├── leaves.py               # Shared leave detail & NLP classification routes
│   └── notifications.py        # In-app notifications API routes
│
├── static/
│   ├── css/style.css           # Glassmorphism SaaS design system & Dark Mode
│   ├── js/main.js              # Navbar, Toast notifications, Theme toggle
│   ├── js/auth.js              # Login, role selection, 6-box OTP input
│   ├── js/nlp.js               # Real-time NLP classifier debounced trigger
│   └── js/dashboard.js         # Chart.js analytics charts
│
├── database/
│   ├── schema.sql              # MySQL DDL table schema
│   └── seed.sql                # Production seed script (Indian student & faculty data)
│
└── templates/
    ├── index.html              # Landing Page
    ├── login.html              # Multi-role Login & TOTP MFA modal
    ├── student_dashboard.html  # Student Portal
    ├── apply_leave.html        # Multi-step leave form with live AI classifier
    ├── request_detail.html     # Leave request detail with vertical approval timeline
    ├── approver_dashboard.html # Faculty Approval Center
    ├── admin_dashboard.html    # Admin Control Center with Chart.js
    ├── admin_users.html        # User Management (Add, Delete, Assign Faculty, Reset MFA)
    ├── admin_roles.html        # RBAC Matrix Editor
    ├── admin_workflow.html     # Visual Approval Workflow builder
    ├── admin_policies.html     # Leave Policies editor
    ├── admin_audit.html        # Audit log viewer with CSV export
    ├── admin_reports.html      # Reports & Analytics
    └── error.html              # Custom 403, 404, 500 error pages
```

---

## 🚀 How to Run in Windows Command Prompt (CMD)

### Step 1: Open Command Prompt
1. Press `Win + R`, type `cmd`, and press `Enter`.
2. Navigate to the extracted project folder:
   ```cmd
   cd "C:\path\to\extracted\folder"
   ```

### Step 2: Create Virtual Environment & Install Dependencies
1. Create a Python virtual environment:
   ```cmd
   python -m venv venv
   ```
2. Activate the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
3. Install required packages:
   ```cmd
   pip install -r requirements.txt
   ```

### Step 3: Start the Web Server
Run the Flask server:
```cmd
python app.py
```

### Step 4: Open in Web Browser
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Demo Login Accounts

| Role | Employee / Staff ID | Password | 6-Digit MFA Code |
| :--- | :--- | :--- | :--- |
| **Student / Employee** | `STU1001` (Aarav Sharma) | `password123` | `123456` |
| **Faculty / Approver** | `FAC2001` (Dr. Rajesh Kumar) | `password123` | `123456` |
| **Admin Control Center** | `ADM3001` (Pushkar Mishra) | `password123` | `123456` |
