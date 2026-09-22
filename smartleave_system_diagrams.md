# SmartLeave — System Diagrams & Architectural Specifications

This document presents the complete, professionally labeled system diagrams for **SmartLeave (Smart Leave Approval Workflow System)**. Every diagram is modeled specifically after the SmartLeave architecture, database schema, AI NLP classification engine, multi-level approval pipeline, and role-based access control.

---

## 1. 🌊 Data Flow Diagrams (DFD)

### 1.1 Context Level DFD (Level 0)
The Context Diagram represents the overall SmartLeave system as a single central process interacting with three external entities: **Student / Employee**, **Faculty / Approver**, and **System Administrator**.

```mermaid
flowchart TD
    %% External Entities
    STU["Student / Employee"]
    FAC["Faculty / Approver"]
    ADM["System Administrator"]

    %% Central Process
    SYS(("0.0<br/>SmartLeave Workflow<br/>Management System"))

    %% Student Data Flows
    STU -->|"1. Credentials & TOTP MFA Code"| SYS
    STU -->|"2. Leave Application (Type, Dates, Reason)"| SYS
    SYS -->|"3. Live AI Category & Confidence Insight"| STU
    SYS -->|"4. Leave Balance & Application Status"| STU
    SYS -->|"5. In-App Approval/Rejection Notifications"| STU

    %% Faculty Data Flows
    FAC -->|"6. Credentials & MFA Authentication"| SYS
    FAC -->|"7. Review Action (Approve / Reject / Forward)"| SYS
    SYS -->|"8. Pending Advisee / Department Queue"| FAC
    SYS -->|"9. Department Analytics & Urgent Request Alerts"| FAC

    %% Admin Data Flows
    ADM -->|"10. Admin Authentication & System Configuration"| SYS
    ADM -->|"11. User Management (Add/Delete/Assign Faculty)"| SYS
    ADM -->|"12. Policy Allowance & Workflow Rules Updates"| SYS
    SYS -->|"13. Escalated Leaves (>3 Days / Urgent)"| ADM
    SYS -->|"14. System Metrics & Immutable Audit Trail CSV"| ADM
```

---

### 1.2 Level 1 DFD — Student / Employee Subsystem
Explodes the Student interactions into detailed sub-processes: Authentication, Leave Application with AI Reason Classification, Balance Tracking, and Notifications.

```mermaid
flowchart TD
    STU["Student / Employee"]

    subgraph Student Subsystem
        P1["1.0<br/>Authenticate & MFA Verification"]
        P2["2.0<br/>Submit Leave Application"]
        P3["3.0<br/>NLP Reason Classifier<br/>(scikit-learn Engine)"]
        P4["4.0<br/>Track Balance & History"]
        P5["5.0<br/>View Notifications"]
    end

    %% Data Stores
    DS_USERS[("D1: Users Store")]
    DS_LEAVES[("D2: Leave Requests Store")]
    DS_POLICIES[("D3: Leave Policies Store")]
    DS_NOTIFS[("D4: Notifications Store")]

    %% Interactions
    STU -->|"Credentials & OTP"| P1
    P1 <-->|"Validate Password Hash & TOTP"| DS_USERS

    STU -->|"Leave Details & Reason Text"| P2
    P2 -->|"Raw Reason String"| P3
    P3 -->|"Predicted Category & Confidence Score"| P2
    P2 -->|"Check Remaining Allowance"| DS_POLICIES
    P2 -->|"Save Request (Pending Status)"| DS_LEAVES

    P4 <-->|"Fetch Applied Leaves & Balance"| DS_LEAVES
    P4 -->|"Display History & Progress Bars"| STU

    P5 <-->|"Fetch Unread Notifications"| DS_NOTIFS
    P5 -->|"Render Alert Toasts"| STU
```

---

### 1.3 Level 1 DFD — Faculty / Approver Subsystem
Explodes the Faculty review operations: Pending Queue fetching, Approval Decision Processing, Notification Dispatching, and Department Statistics.

```mermaid
flowchart TD
    FAC["Faculty / Approver"]

    subgraph Faculty Subsystem
        F1["1.0<br/>Authenticate Approver"]
        F2["2.0<br/>Fetch Pending Advisee Queue"]
        F3["3.0<br/>Process Approval Action<br/>(Approve / Reject / Forward)"]
        F4["4.0<br/>Generate Notifications & Audit"]
    end

    DS_USERS[("D1: Users Store")]
    DS_LEAVES[("D2: Leave Requests Store")]
    DS_STEPS[("D5: Approval Steps Store")]
    DS_NOTIFS[("D4: Notifications Store")]
    DS_AUDIT[("D6: Audit Logs Store")]

    FAC -->|"Login & MFA Code"| F1
    F1 <-->|"Verify Faculty Credentials"| DS_USERS

    FAC -->|"Request Pending Requests"| F2
    F2 <-->|"Fetch Leaves matching Advisee ID / Dept ID"| DS_LEAVES
    F2 -->|"Render Approver Queue"| FAC

    FAC -->|"Action: Approve / Reject / Forward + Remarks"| F3
    F3 -->|"Update Request Status & Current Level"| DS_LEAVES
    F3 -->|"Log Decision Step"| DS_STEPS
    F3 -->|"Trigger State Changes"| F4

    F4 -->|"Create Alert for Student"| DS_NOTIFS
    F4 -->|"Record Immutable Event"| DS_AUDIT
```

---

### 1.4 Level 1 DFD — Admin Subsystem
Models Administrative processes: System Control, User Account CRUD & 1-Faculty-to-Multiple-Students Assignment, Policy Configuration, Workflow Escalation, and Audit Trail.

```mermaid
flowchart TD
    ADM["System Administrator"]

    subgraph Admin Subsystem
        A1["1.0<br/>Admin Control Center"]
        A2["2.0<br/>User Management & Faculty Allocation"]
        A3["3.0<br/>Manage Policies & Workflow Rules"]
        A4["4.0<br/>Escalated Requests Review"]
        A5["5.0<br/>Audit Trail & Report Export"]
    end

    DS_USERS[("D1: Users Store")]
    DS_LEAVES[("D2: Leave Requests Store")]
    DS_POLICIES[("D3: Leave Policies Store")]
    DS_AUDIT[("D6: Audit Logs Store")]

    ADM -->|"Admin Credentials"| A1
    A1 <-->|"Verify Admin Role"| DS_USERS

    ADM -->|"Create/Delete User, Assign Faculty Advisor"| A2
    A2 <-->|"UPDATE users SET advisor_id"| DS_USERS
    A2 -->|"Log USER_DELETE / ASSIGN_FACULTY"| DS_AUDIT

    ADM -->|"Modify Allowances & Rules"| A3
    A3 <-->|"Update Thresholds"| DS_POLICIES

    ADM -->|"Review Escalated (>3 Days / Urgent)"| A4
    A4 <-->|"Fetch & Update Level = Admin Requests"| DS_LEAVES

    A5 <-->|"Read & Export Audit Trail to CSV"| DS_AUDIT
    A5 -->|"Download CSV Report"| ADM
```

---

### 1.5 Level 2 DFD — Leave Approval & AI Classification Pipeline
Detailed Level 2 Data Flow Diagram illustrating the internal mechanics of Leave Submission, TF-IDF NLP Categorization, Escalation Engine, and Approval Pipeline.

```mermaid
flowchart TD
    STU["Student"]
    FAC["Faculty Approver"]
    ADM["Admin"]

    subgraph "2.0 Leave Submission & Routing Engine"
        P2_1["2.1 Parse Input & Validate Dates"]
        P2_2["2.2 Compute Total Days (Date Math)"]
        P2_3["2.3 TF-IDF Vectorization & MultinomialNB Model"]
        P2_4["2.4 Evaluate Escalation Rules Engine"]
        P2_5["2.5 Persist Request & Dispatch Task"]
    end

    DS_LEAVES[("D2: Leave Requests")]
    DS_STEPS[("D5: Approval Steps")]
    DS_NOTIFS[("D4: Notifications")]
    DS_AUDIT[("D6: Audit Logs")]

    STU -->|"Leave Type, Start Date, End Date, Reason Text"| P2_1
    P2_1 --> P2_2
    P2_2 -->|"Days Count"| P2_3
    P2_3 -->|"Reason Text"| P2_3
    P2_3 -->|"Category: Medical/Personal/Urgent & Confidence Score"| P2_4

    P2_4 -->|"If Days > 3 OR Category == Urgent -> Level: Admin"| P2_5
    P2_4 -->|"Else -> Level: Faculty (Check advisor_id)"| P2_5

    P2_5 -->|"INSERT INTO leave_requests"| DS_LEAVES
    P2_5 -->|"Notify Approver"| DS_NOTIFS
    P2_5 -->|"Log SUBMIT_LEAVE"| DS_AUDIT

    FAC -->|"Review & Submit Decision"| DS_STEPS
    DS_STEPS -->|"Update Status"| DS_LEAVES
    DS_LEAVES -->|"Notify Result"| STU
```

---

## 2. 👤 Use Case Diagrams

### 2.1 Complete System Use Case Overview
Provides a unified view of all system use cases grouped by actor roles.

```mermaid
flowchart LR
    subgraph Actors
        Student["👨‍🎓 Student / Employee"]
        Faculty["👨‍🏫 Faculty / Approver"]
        Admin["👨‍💼 Administrator"]
    end

    subgraph "SmartLeave Application Boundary"
        %% Shared Authentication
        UC_Login(("UC-1: Login & MFA Verification"))
        UC_Logout(("UC-2: Logout"))
        UC_Profile(("UC-3: View Profile"))

        %% Student Use Cases
        UC_Apply(("UC-4: Submit Leave Application"))
        UC_LiveAI(("UC-5: Live AI Reason Insight"))
        UC_TrackBal(("UC-6: View Leave Balance & History"))
        UC_ViewDetail(("UC-7: View Request Timeline"))
        UC_Notifs(("UC-8: Receive In-App Notifications"))

        %% Faculty Use Cases
        UC_Queue(("UC-9: View Advisee Pending Queue"))
        UC_Approve(("UC-10: Approve Leave Request"))
        UC_Reject(("UC-11: Reject Leave Request"))
        UC_Forward(("UC-12: Forward Request to Admin"))
        UC_FacultyStats(("UC-13: View Department Metrics"))

        %% Admin Use Cases
        UC_AdminDash(("UC-14: System Overview & Analytics"))
        UC_UserCRUD(("UC-15: Manage Users (Add/Edit/Delete)"))
        UC_AssignFac(("UC-16: Assign 1 Faculty to Multiple Students"))
        UC_ResetMFA(("UC-17: Reset User MFA Secrets"))
        UC_Policies(("UC-18: Manage Leave Policies"))
        UC_Workflow(("UC-19: Configure Workflow Rules"))
        UC_Audit(("UC-20: View & Export Audit Trail to CSV"))
    end

    %% Actor Associations
    Student --> UC_Login
    Student --> UC_Logout
    Student --> UC_Profile
    Student --> UC_Apply
    Student --> UC_LiveAI
    Student --> UC_TrackBal
    Student --> UC_ViewDetail
    Student --> UC_Notifs

    Faculty --> UC_Login
    Faculty --> UC_Logout
    Faculty --> UC_Profile
    Faculty --> UC_Queue
    Faculty --> UC_Approve
    Faculty --> UC_Reject
    Faculty --> UC_Forward
    Faculty --> UC_FacultyStats
    Faculty --> UC_Notifs

    Admin --> UC_Login
    Admin --> UC_Logout
    Admin --> UC_AdminDash
    Admin --> UC_UserCRUD
    Admin --> UC_AssignFac
    Admin --> UC_ResetMFA
    Admin --> UC_Policies
    Admin --> UC_Workflow
    Admin --> UC_Audit
```

---

## 3. 📐 Unified Class Diagram

Detailed UML Class Diagram illustrating object-oriented domain entities, services, relationships, attributes, and methods in the SmartLeave architecture.

```mermaid
classDiagram
    class User {
        +int id
        +string employee_id
        +string name
        +string email
        +string password_hash
        +int role_id
        +int department_id
        +string mfa_secret
        +int mfa_enabled
        +string status
        +int advisor_id
        +datetime last_login
        +get_by_id(user_id) User
        +get_by_employee_id(emp_id) User
        +authenticate(emp_id, password) User
        +get_all_users() List~User~
        +get_faculty_members() List~User~
        +get_students() List~User~
        +create_user(emp_id, name, email, password, role_id, dept_id) int
        +assign_faculty_to_students(faculty_id, student_ids) bool
        +delete_user(user_id) bool
        +reset_mfa_secret(user_id, secret) bool
    }

    class LeaveRequest {
        +int id
        +string request_number
        +int user_id
        +string leave_type
        +date start_date
        +date end_date
        +int total_days
        +string reason
        +string ai_category
        +float ai_confidence
        +string status
        +string current_level
        +datetime created_at
        +create_request(data) int
        +get_by_id(request_id) LeaveRequest
        +get_by_user_id(user_id) List~LeaveRequest~
        +get_pending_for_approver(role, dept_id, approver_id) List~LeaveRequest~
        +update_status(request_id, status, level) bool
    }

    class ApprovalStep {
        +int id
        +int request_id
        +int approver_id
        +string level
        +string status
        +string comments
        +datetime action_date
        +record_step(request_id, approver_id, level, status, comments) int
        +get_steps_by_request(request_id) List~ApprovalStep~
    }

    class LeavePolicy {
        +int id
        +string leave_type
        +int allowance
        +int max_consecutive_days
        +int department_id
        +int active
        +get_all() List~LeavePolicy~
        +get_by_type(leave_type) LeavePolicy
        +update_policy(id, allowance, max_days) bool
    }

    class Notification {
        +int id
        +int user_id
        +string title
        +string message
        +int is_read
        +datetime created_at
        +create(user_id, title, message) int
        +get_by_user(user_id) List~Notification~
        +mark_as_read(notif_id) bool
    }

    class AuditLog {
        +int id
        +int user_id
        +string action
        +string target_entity
        +int target_id
        +string details
        +string ip_address
        +datetime timestamp
        +log(user_id, action, entity, target_id, details) int
        +get_recent(limit) List~AuditLog~
    }

    class NLPClassifier {
        +TfidfVectorizer vectorizer
        +MultinomialNB model
        +train()
        +classify_reason(text) Dict
    }

    class AuthService {
        +verify_password(user, password) bool
        +verify_totp(secret, code) bool
        +generate_mfa_qr(secret, email) string
    }

    class WorkflowEngine {
        +determine_routing(total_days, ai_category) string
        +should_escalate_to_admin(total_days, ai_category) bool
    }

    %% Class Relationships
    User "1" -- "0..*" LeaveRequest : submits
    User "1" -- "0..*" ApprovalStep : executes
    User "1" -- "0..*" Notification : receives
    User "1" -- "0..*" AuditLog : triggers
    User "1" -- "0..*" User : advises (1 Faculty to N Students)
    LeaveRequest "1" -- "0..*" ApprovalStep : tracks
    LeavePolicy "1" -- "0..*" LeaveRequest : governs
    NLPClassifier ..> LeaveRequest : categorizes
    WorkflowEngine ..> LeaveRequest : routes
    AuthService ..> User : authenticates
```

---

## 4. 🔄 Activity Diagrams

### 4.1 Student Activity Flow (Submit Leave & View Insight)

```mermaid
stateDiagram-v2
    [*] --> StudentLogin: Enter Credentials & 6-Digit TOTP MFA
    StudentLogin --> AuthCheck: Verify MFA
    AuthCheck --> StudentLogin: Invalid Code
    AuthCheck --> StudentDashboard: Valid Auth

    StudentDashboard --> ClickApplyLeave: Click "+ Apply for Leave"
    ClickApplyLeave --> FormInput: Select Leave Type, Start & End Dates
    FormInput --> DateCalculation: Auto-calculate Total Days

    FormInput --> TypeReason: Type Reason Text
    TypeReason --> LiveAIInsight: Debounced API Request (300ms)
    LiveAIInsight --> RenderBadge: Display AI Category (Medical/Personal/Urgent) & Confidence %

    RenderBadge --> SubmitForm: Click "Submit Application"
    SubmitForm --> PolicyCheck: Check Leave Balance & Max Days Limit

    PolicyCheck --> RejectForm: Exceeds Balance Limit
    RejectForm --> FormInput: Display Toast Error

    PolicyCheck --> SaveRequest: Pass Balance Check
    SaveRequest --> EvaluateEscalation: Workflow Routing Engine

    EvaluateEscalation --> RouteFaculty: Days <= 3 AND Category != Urgent
    EvaluateEscalation --> RouteAdmin: Days > 3 OR Category == Urgent

    RouteFaculty --> PersistDB: Current Level = Faculty
    RouteAdmin --> PersistDB: Current Level = Admin

    PersistDB --> SendNotif: Notify Approver
    SendNotif --> AuditRecord: Log SUBMIT_LEAVE Audit Event
    AuditRecord --> RedirectDashboard: Show Success Toast & Redirect
    RedirectDashboard --> [*]
```

---

### 4.2 Faculty / Approver Activity Flow (Review & Process Requests)

```mermaid
stateDiagram-v2
    [*] --> ApproverLogin: Enter Approver Credentials & MFA
    ApproverLogin --> VerifyRole: Check Faculty Role
    VerifyRole --> ApproverDashboard: Load Advisee & Department Queue

    ApproverDashboard --> SelectRequest: Click "Review Request"
    SelectRequest --> RenderModal: Display Student History, Dates & AI Badge

    RenderModal --> DecisionNode: Approver Choice

    DecisionNode --> ApproveBranch: Click "Approve"
    ApproveBranch --> UpdateApproved: Status = Approved, Level = Completed
    UpdateApproved --> DeductBalance: Update User Leave Balance

    DecisionNode --> RejectBranch: Click "Reject"
    RejectBranch --> PromptComment: Enter Mandatory Rejection Reason
    PromptComment --> UpdateRejected: Status = Rejected, Level = Completed

    DecisionNode --> ForwardBranch: Click "Forward to Admin"
    ForwardBranch --> EnterForwardNotes: Enter Forwarding Remarks
    EnterForwardNotes --> UpdateForwarded: Status = Forwarded, Level = Admin

    DeductBalance --> SaveStep: Insert into approval_steps
    UpdateRejected --> SaveStep: Insert into approval_steps
    UpdateForwarded --> SaveStep: Insert into approval_steps

    SaveStep --> NotifyStudent: Trigger Student In-App Notification
    NotifyStudent --> AuditLog: Log APPROVE/REJECT/FORWARD Event
    AuditLog --> RefreshQueue: Refresh Approver Dashboard
    RefreshQueue --> [*]
```

---

### 4.3 Admin Activity Flow (User CRUD & 1-Faculty-to-Multiple-Students Assignment)

```mermaid
stateDiagram-v2
    [*] --> AdminLogin: Authenticate Admin Account (Pushkar Mishra)
    AdminLogin --> LoadAdminPanel: Open Control Center

    LoadAdminPanel --> SelectTab: Choose Admin Action

    state SelectTab {
        [*] --> UserManagement
        [*] --> AssignFaculty
        [*] --> DeleteUser
        [*] --> ExportAudit
    }

    UserManagement --> OpenAddModal: Click "+ Add New User"
    OpenAddModal --> FillDetails: Enter Employee ID, Name, Email, Role, Dept
    FillDetails --> CreateUser: POST /api/admin/users
    CreateUser --> UserLog: Log CREATE_USER

    AssignFaculty --> OpenAssignModal: Click "Assign Faculty to Multiple Students"
    OpenAssignModal --> FetchList: GET /api/admin/faculty-assignments
    FetchList --> SelectFac: Select 1 Faculty Approver from Dropdown
    SelectFac --> CheckStudents: Check Multiple Students (Select All option)
    CheckStudents --> SubmitAssign: POST /api/admin/assign-faculty
    SubmitAssign --> UpdateAdvisorID: UPDATE users SET advisor_id = faculty_id
    UpdateAdvisorID --> AssignLog: Log ASSIGN_FACULTY

    DeleteUser --> ClickDelete: Click "Delete User" on table row
    ClickDelete --> ConfirmModal: Confirm Deletion Prompt
    ConfirmModal --> ExecuteDelete: DELETE /api/admin/users/<id>
    ExecuteDelete --> CascadeCleanup: Cascade Delete Requests & Steps
    CascadeCleanup --> DeleteLog: Log DELETE_USER

    ExportAudit --> OpenAuditPage: Navigate to Audit Trail
    OpenAuditPage --> ClickCSV: Click "Export Audit Logs CSV"
    ClickCSV --> DownloadFile: Generate & Stream CSV File

    UserLog --> RefreshUI: Toast Notification & Page Refresh
    AssignLog --> RefreshUI
    DeleteLog --> RefreshUI
    DownloadFile --> [*]
    RefreshUI --> [*]
```

---

## 5. 🗄️ Entity-Relationship (ER) Diagram

Complete Relational Entity-Relationship Diagram representing the database schema for SmartLeave (`smartleave.db` / `database/schema.sql`).

```mermaid
erDiagram
    users ||--o{ leave_requests : "submits (1:N)"
    users ||--o{ approval_steps : "executes (1:N)"
    users ||--o{ notifications : "receives (1:N)"
    users ||--o{ audit_logs : "triggers (1:N)"
    users ||--o{ users : "advises (1 Faculty to N Students)"
    roles ||--o{ users : "defines (1:N)"
    departments ||--o{ users : "belongs_to (1:N)"
    departments ||--o{ leave_policies : "applies_to (1:N)"
    roles ||--o{ role_permissions : "has (1:N)"
    permissions ||--o{ role_permissions : "granted_in (1:N)"
    leave_requests ||--o{ approval_steps : "tracked_by (1:N)"

    users {
        int id PK
        string employee_id UK
        string name
        string email UK
        string password_hash
        int role_id FK
        int department_id FK
        string mfa_secret
        int mfa_enabled
        string status
        int advisor_id FK "References users(id)"
        timestamp created_at
        timestamp last_login
    }

    roles {
        int id PK
        string name UK
        string description
    }

    permissions {
        int id PK
        string name UK
        string description
    }

    role_permissions {
        int role_id PK, FK
        int permission_id PK, FK
    }

    departments {
        int id PK
        string name UK
        string code UK
        timestamp created_at
    }

    leave_policies {
        int id PK
        string leave_type
        int allowance
        int max_consecutive_days
        int department_id FK
        int active
    }

    leave_requests {
        int id PK
        string request_number UK
        int user_id FK
        string leave_type
        date start_date
        date end_date
        int total_days
        string reason
        string ai_category
        float ai_confidence
        string status
        string current_level
        timestamp created_at
        timestamp updated_at
    }

    approval_steps {
        int id PK
        int request_id FK
        int approver_id FK
        string level
        string status
        string comments
        timestamp action_date
    }

    notifications {
        int id PK
        int user_id FK
        string title
        string message
        int is_read
        timestamp created_at
    }

    audit_logs {
        int id PK
        int user_id FK
        string action
        string target_entity
        int target_id
        string details
        string ip_address
        timestamp timestamp
    }
```

---

## 📋 Diagram Reference & Verification Summary

| Diagram | Description & Coverage | Format / Tool |
| :--- | :--- | :--- |
| **0.0 Context DFD** | High-level interactions between Student, Faculty, Admin, and SmartLeave. | Mermaid Flowchart |
| **1.1 Student DFD** | Subsystem operations: Auth, Apply, Live AI Classifier, Balance, Notifications. | Mermaid Flowchart |
| **1.2 Faculty DFD** | Subsystem operations: Auth, Advisee Queue, Approve/Reject/Forward, Audit. | Mermaid Flowchart |
| **1.3 Admin DFD** | Subsystem operations: Control Center, User CRUD, Assign Faculty, Policy, Audit. | Mermaid Flowchart |
| **2.0 Level 2 DFD** | Detailed submission, TF-IDF NLP classification, routing rules, and persistence. | Mermaid Flowchart |
| **Use Case Diagram** | Complete system boundary with Student, Faculty, and Admin use cases. | Mermaid Diagram |
| **Class Diagram** | UML class diagram showing domain models, services, attributes, and methods. | Mermaid Class Diagram |
| **Activity Diagrams** | Behavioral state diagrams for Student, Faculty, and Admin workflows. | Mermaid State Diagram |
| **ER Diagram** | Full relational database schema with PK/FK constraints and cardinality. | Mermaid ER Diagram |
