# MINI PROJECT DEVELOPMENT PHASE 2 & 3 REPORT
## SmartLeave — Smart Leave Approval Workflow System

---

### 📌 Project Overview & Metadata

- **Project Title**: SmartLeave — Smart Leave Approval Workflow System
- **Tagline**: *"Leave management, intelligently simplified."*
- **Phase**: Development Phase 2 & 3 (Layout/Form Design with Working Code, Database Connectivity, and CRUD Operations)
- **Submission Date**: 28th August 2026
- **Student Name / Author**: Pushkar Mishra
- **Technology Stack**:
  - **Frontend**: HTML5, CSS3 Glassmorphism System, Vanilla JavaScript (ES6+), Chart.js Analytics, Font Awesome Icons
  - **Backend**: Python 3.13, Flask REST API Framework, Flask Sessions & RBAC
  - **Security**: Password Hashing (`werkzeug.security`), TOTP-based 2FA (`pyotp`), Server-side Authorization Checks
  - **Database**: SQLite (Development / Standalone) & MySQL Relational Schema (`database/schema.sql` & `database/seed.sql`)
  - **AI / NLP Engine**: `scikit-learn` TF-IDF Vectorizer + Multinomial Naive Bayes / Logistic Regression Reason Classifier

---

## 1. 🏗️ Architecture & Module Organization

The application strictly adheres to the Model-View-Controller (MVC) and Service-Layer software design patterns:

```text
smartleave/
├── app.py                      # Flask Application entry point & route controllers
├── config.py                   # Central Configuration Management
├── requirements.txt            # Python dependencies manifest
├── smartleave.db               # SQLite pre-populated database
├── README.md                   # Comprehensive Setup & Installation Guide
│
├── models/                     # Data Access Objects & Relational Schemas
│   ├── database.py             # Database connector (Dual MySQL / SQLite support with auto-seed)
│   ├── user.py                 # User authentication, RBAC, and Faculty assignment model
│   ├── leave.py                # Leave request & policy calculation model
│   ├── approval.py             # Multi-level approval steps tracking model
│   └── audit.py                # System audit trail logger model
│
├── services/                   # Business Logic & Service Abstraction Layer
│   ├── auth_service.py         # Password verification & TOTP MFA generation
│   ├── leave_service.py        # Leave submission, state transitions, & balance calculation
│   ├── workflow_service.py     # Routing engine (>3 days / Urgent -> Admin escalation)
│   ├── nlp_service.py          # scikit-learn TF-IDF reason classification
│   ├── notification_service.py # In-app notification creation & read management
│   └── audit_service.py        # Activity logging wrapper
│
├── routes/                     # REST API Endpoints & Blueprints
│   ├── auth.py                 # /api/auth (Login, TOTP, Logout, Session check)
│   ├── student.py              # /api/student (Dashboard stats, requests list)
│   ├── approver.py             # /api/approver (Pending queue, statistics)
│   ├── admin.py                # /api/admin (Users CRUD, Delete, Assign Faculty, Audit export)
│   ├── leaves.py               # /api/leaves (Submit, Classify reason, Approve/Reject/Forward)
│   └── notifications.py        # /api/notifications (Read status toggle)
│
├── static/                     # Assets & Client-Side Scripts
│   ├── css/style.css           # SaaS design system, CSS variables, Dark Mode, Animations
│   ├── js/main.js              # Toast notifications, Dark mode, Topbar notification bell
│   ├── js/auth.js              # Role tab switching & 6-digit OTP box input
│   ├── js/nlp.js               # Debounced NLP classification trigger & UI badge
│   └── js/dashboard.js         # Chart.js analytics visualizations
│
└── templates/                  # Responsive HTML5 Templates
    ├── index.html              # Public Landing Page
    ├── login.html              # Multi-role Login & TOTP MFA modal
    ├── student_dashboard.html  # Student Portal (Stats, balance progress, history)
    ├── apply_leave.html        # Multi-step leave form with live AI classifier
    ├── request_detail.html     # Request tracking with vertical approval timeline
    ├── approver_dashboard.html # Faculty Approval Center
    ├── admin_dashboard.html    # Admin Control Center with Chart.js
    ├── admin_users.html        # User Management & 1-Faculty-to-Multiple-Students Assignment UI
    ├── admin_roles.html        # Role-Based Access Control (RBAC) Matrix
    ├── admin_workflow.html     # Visual Approval Workflow Builder
    ├── admin_policies.html     # Leave Policy Editor
    ├── admin_audit.html        # Immutable Audit Logs viewer with CSV export
    ├── admin_reports.html      # Reports & Analytics Center
    └── error.html              # Custom 403, 404, 500 Error Handler Page
```

---

## 2. 🎨 UI & Form Design Implementation (Phase 2 & 3)

### 2.1 Landing Page (`templates/index.html`)
- **Hero Section**: Headline *"Smart Leave Management for Modern Institutions"*, Call-to-Action buttons, and animated preview mockup.
- **Interactive Feature Cards**: Explaining Smart Applications, Automated Routing, AI Classification, and Real-Time Analytics.
- **Visual Workflow Sequence**: Animated step-by-step pipeline (`Apply` → `AI Classify` → `Faculty Review` → `Decision & Audit`).

### 2.2 Multi-Role Authentication & TOTP MFA (`templates/login.html` & `static/js/auth.js`)
- **Role Tabs**: Instant switching between `Student/Employee`, `Faculty/Approver`, and `Admin`.
- **Password Visibility Toggle**: Interactive eye icon to show/hide password text.
- **6-Digit OTP Box UI**: Auto-focusing 6-box TOTP verification interface with paste support and countdown timer.

### 2.3 Multi-Step Leave Application Form (`templates/apply_leave.html`)
- **Stepper Header**: `01 Details` → `02 Reason` → `03 Review` → `04 Submit`.
- **Dynamic Date Math**: Auto-calculates total days when start and end dates are picked.
- **Live AI Reason Insight**: As the user types their leave reason, a debounced API request classifies the text into `Medical`, `Personal`, or `Urgent` with confidence scoring.

### 2.4 Faculty Approval Center (`templates/approver_dashboard.html`)
- **Urgent Request Highlighting**: High-priority urgent requests are highlighted with a red accent border.
- **Interactive Review Modal**: Allows Faculty to **Approve**, **Reject** (with mandatory reason), or **Forward to Admin**.

### 2.5 Admin Control Center & User Assignment (`templates/admin_users.html`)
- **User CRUD & Deletion**: Complete user table with search, role display, TOTP reset, and permanent user deletion with audit logging.
- **1-Faculty to Multiple-Students Assignment UI**: Interactive modal enabling the Admin to select 1 Faculty member and assign them to multiple selected students simultaneously.

---

## 3. 🗄️ Database Design & Connectivity (Phase 3)

### 3.1 Relational Entity-Relationship Structure
1. **`users`**: Stores employee ID, hashed password, role ID, department ID, MFA secret, status, and assigned `advisor_id` (Foreign Key to `users.id`).
2. **`roles` & `permissions`**: Role-based permissions mapping (`Student/Employee`, `Faculty/Approver`, `Admin`).
3. **`departments`**: Institutional departments (`CSE`, `IT`, `ECE`, `EE`, `ME`, `ADMIN`).
4. **`leave_policies`**: Annual allowances and maximum consecutive day thresholds per leave type.
5. **`leave_requests`**: Stores request number, user ID, leave type, start/end dates, total days, reason, AI category, confidence, status (`Pending`, `Approved`, `Rejected`, `Forwarded`), and current level.
6. **`approval_steps`**: Tracks approval action history (Approver ID, level, status, comments, action timestamp).
7. **`notifications`**: User notification history with unread status flags.
8. **`audit_logs`**: Immutable security log of user logins, leave submissions, approvals, user creations/deletions, and faculty assignments.

---

## 4. ⚡ Working CRUD Operations Summary

| Operation | Entity | Description & Endpoint |
| :--- | :--- | :--- |
| **Create** | Leave Application | `POST /api/leaves` — Submits new request with AI classification |
| **Create** | User Account | `POST /api/admin/users` — Creates new student, faculty, or admin user |
| **Read** | User Dashboard / Requests | `GET /api/student/dashboard`, `GET /api/leaves/<id>` — Fetches user leave balance & timeline |
| **Read** | Approver Queue | `GET /api/approver/dashboard` — Fetches pending requests for assigned advisees / department |
| **Update** | Leave Status | `POST /api/leaves/<id>/approve`, `/reject`, `/forward` — Updates leave state & balance |
| **Update** | Faculty Assignment | `POST /api/admin/assign-faculty` — Assigns 1 Faculty member to multiple students |
| **Update** | Leave Policy | `PUT /api/admin/policies` — Updates annual allowance & max consecutive days |
| **Delete** | User Account | `DELETE /api/admin/users/<id>` — Permanently deletes user with cascade cleanup |

---

## 5. 🛠️ Installation & Setup Guide

### 1. Requirements
- Python 3.10+ installed
- Windows Command Prompt (CMD) or PowerShell

### 2. Execution Steps
```cmd
# 1. Navigate to the project directory
cd "C:\path\to\SmartLeave"

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Launch web server
python app.py
```

### 3. Verification
Open your web browser and visit: **`http://127.0.0.1:5000`**

---

## 🔑 Pre-Configured Demo Credentials

| Role | Employee / Staff ID | Password | 6-Digit MFA Code | Name |
| :--- | :--- | :--- | :--- | :--- |
| **Student / Employee** | `STU1001` | `password123` | `123456` | Aarav Sharma |
| **Faculty / Approver** | `FAC2001` | `password123` | `123456` | Dr. Rajesh Kumar |
| **Admin Control Center** | `ADM3001` | `password123` | `123456` | Pushkar Mishra |

---

## ✅ Pre-Submission Checklist Verification

- [x] **All forms designed & functional**: Multi-step leave form, Login/MFA form, User creation form, Review modal.
- [x] **Database created & connected**: SQLite `smartleave.db` active with MySQL DDL backup scripts.
- [x] **CRUD operations working**: Create, Read, Update, and Delete verified via automated test suite.
- [x] **Code compiles/runs without errors**: Clean Flask initialization and zero syntax/runtime errors.
- [x] **Documentation complete**: Code comments present, architecture documented, progress report generated.
- [x] **README & setup guide included**: CMD and PowerShell step-by-step instructions detailed in `README.md`.
