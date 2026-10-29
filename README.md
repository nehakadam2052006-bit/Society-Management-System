# Central Park Housing Society Management System

A simple, modern, full-featured web portal for residential housing societies built with **Python Flask**, **SQLite / MySQL**, and **Bootstrap 5**, accompanied by a complete **University Blackbook Project Report PDF** formatted in accordance with Mumbai University standards.

---

## 🚀 Quick Start (Run Locally in 1 Minute)

### 1. Activate Environment & Run
```bash
# If using the existing virtual environment:
./venv/bin/python app.py

# Or with system python3:
python3 app.py
```

Open your browser and navigate to:
👉 **[http://127.0.0.1:5001](http://127.0.0.1:5001)**

---

## 🔑 Demo Logins (1-Click Buttons on Login Page)

| Role | Username | Password | Purpose & Capabilities |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full Society Control: Flats, Residents, Billing, Maintenance, Complaints, Notices, Vehicles & CSV Exports |
| **Resident** | `resident` | `resident123` | Resident Portal (Flat A-101): View Dues, Instant Online Payment, Printable Receipts, Lodge Complaints & Circulars |
| **Security** | `security` | `security123` | Gatekeeper Console: Fast Visitor Entry Pass, Live In-Premises Tracking, and 1-Click Departure (EXIT) Logging |

*(The login screen also features 1-click Quick Login demo buttons that automatically fill and submit the credentials).*

---

## 📄 Blackbook Project Report PDF

The complete academic Blackbook project report has been generated:
📁 **[`Society_Management_System_Project_Report.pdf`](file:///Users/manavsingh/Desktop/Society%20management/Society_Management_System_Project_Report.pdf)**

### Key Highlights of the Report:
- **Format:** Identical to the college template (`CampusConnect_Project_Report.pdf`).
- **College Header & Logo:** Model College of Science and Commerce, Kalyan (Affiliated to University of Mumbai).
- **Preliminary Pages:** Title Page, Proforma for Approval of Project Proposal, Certificate of Approval with official college crest, Role & Responsibility Form, Abstract, Acknowledgement, Table of Contents, and List of Figures & Tables.
- **Formal System Diagrams:**
  1. *Figure 1:* Entity-Relationship (ER) Diagram
  2. *Figure 2:* DFD Level 0 (Context Level Diagram)
  3. *Figure 3:* DFD Level 1 (Process Decomposition & Stores)
  4. *Figure 4:* UML Use Case Diagram
  5. *Figure 5:* Three-Tier System Architecture Diagram
  6. *Figure 6:* System Flowchart (Complaint & Maintenance Lifecycle)
- **Live System Screenshots:** 15 high-resolution UI screenshots (Figures 7 to 21) capturing every screen across Admin, Resident, and Security workflows.
- **Academic Chapters:** All 7 standard chapters (Introduction, Survey of Technologies, Requirements & Analysis, System Design, Implementation & Testing with test cases table, Results & Discussion with user documentation, Conclusions & Future Scope), plus References, Glossary, and Appendices.

---

## ⚙️ Project File Structure

```text
Society management/
│
├── app.py                                   # Main Flask Web Server & API Controllers
├── db.py                                    # Dual-engine Relational Database Layer (SQLite / MySQL)
├── config.py                                # System Configuration & Environment Variables
├── init_db.py                               # Standalone Database Initializer Script
├── requirements.txt                         # Python Dependencies & Libraries
│
├── Society_Management_System_Project_Report.pdf # Final Blackbook Project Report (PDF)
├── CampusConnect_Project_Report.pdf         # Reference College Template
│
├── build_project_report.py                  # ReportLab Script to recompile Blackbook PDF
├── generate_diagrams.py                     # Script to generate ER, DFD, UseCase & Architecture diagrams
├── capture_screenshots.py                   # Chrome Headless automated screenshot capturer
│
├── database/
│   ├── schema.sql                           # MySQL / SQLite Relational Database DDL Schema
│   └── society.db                           # Portable Local SQLite Database (Auto-initialized)
│
├── templates/
│   ├── base.html                            # Master responsive layout with sidebar and top navbar
│   ├── login.html                           # Authentication page with 1-click demo role switcher
│   ├── admin_dashboard.html                 # Administrator control center with KPI metric cards
│   ├── flats.html                           # Flat directory & occupancy management
│   ├── residents.html                       # Resident profile & tenancy directory
│   ├── maintenance.html                     # Monthly maintenance assessment & billing console
│   ├── receipt.html                         # Computer-generated printable society payment receipt
│   ├── complaints.html                      # Complaints management & resolution interface
│   ├── visitors.html                        # Real-time visitor log & gate tracking
│   ├── notices.html                         # Digital notice board & circular publisher
│   ├── vehicles.html                        # Resident vehicle directory & parking allocations
│   ├── reports.html                         # Financial summary & CSV spreadsheet export center
│   ├── resident_dashboard.html              # Resident personal flat dashboard & reminders
│   ├── resident_bills.html                  # Resident bill payments & receipt view
│   ├── resident_complaints.html             # Resident complaint submission & resolution tracker
│   └── security_dashboard.html              # Security guard fast gate pass console
│
├── static/
│   ├── css/style.css                        # Custom styling & responsive layouts
│   └── js/                                  # Client-side scripts
│
└── report_assets/
    ├── diagrams/                            # Generated 300-DPI System Engineering Diagrams (Fig 1-6)
    └── screenshots/                         # Captured High-Resolution UI Screenshots (Fig 7-21)
```
