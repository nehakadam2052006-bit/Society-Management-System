import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs('report_assets/diagrams', exist_ok=True)

# -------------------------------------------------------------------
# Figure 1: Entity-Relationship Diagram (ER Diagram)
# -------------------------------------------------------------------
def generate_er_diagram():
    fig, ax = plt.subplots(figsize=(13, 9.5), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Color palette
    box_color = '#EBF3FA'
    border_color = '#1E3A8A'
    pk_color = '#991B1B'
    fk_color = '#065F46'
    rel_color = '#F59E0B'

    # Entities with attributes
    entities = {
        'USERS': (1.0, 6.8, 2.5, 2.6, [
            ('id', 'INT (PK)', pk_color),
            ('username', 'VARCHAR', None),
            ('password', 'VARCHAR', None),
            ('role', 'ENUM', None),
            ('full_name', 'VARCHAR', None),
            ('created_at', 'DATETIME', None)
        ]),
        'FLATS': (5.2, 6.8, 2.6, 2.8, [
            ('id', 'INT (PK)', pk_color),
            ('flat_number', 'VARCHAR', None),
            ('wing', 'VARCHAR', None),
            ('floor', 'INT', None),
            ('flat_type', 'VARCHAR', None),
            ('owner_name', 'VARCHAR', None),
            ('status', 'ENUM', None)
        ]),
        'RESIDENTS': (9.5, 6.8, 2.6, 2.8, [
            ('id', 'INT (PK)', pk_color),
            ('user_id', 'INT (FK)', fk_color),
            ('flat_id', 'INT (FK)', fk_color),
            ('name', 'VARCHAR', None),
            ('mobile', 'VARCHAR', None),
            ('email', 'VARCHAR', None),
            ('resident_type', 'ENUM', None)
        ]),
        'MAINTENANCE': (1.0, 2.8, 2.6, 3.0, [
            ('id', 'INT (PK)', pk_color),
            ('flat_id', 'INT (FK)', fk_color),
            ('month_year', 'VARCHAR', None),
            ('maint_amount', 'DECIMAL', None),
            ('parking_amount', 'DECIMAL', None),
            ('total_amount', 'DECIMAL', None),
            ('status', 'ENUM', None)
        ]),
        'PAYMENTS': (5.2, 2.8, 2.6, 2.8, [
            ('id', 'INT (PK)', pk_color),
            ('maintenance_id', 'INT (FK)', fk_color),
            ('flat_id', 'INT (FK)', fk_color),
            ('amount_paid', 'DECIMAL', None),
            ('payment_mode', 'VARCHAR', None),
            ('receipt_no', 'VARCHAR', None),
            ('payment_date', 'DATETIME', None)
        ]),
        'COMPLAINTS': (9.5, 2.8, 2.6, 3.0, [
            ('id', 'INT (PK)', pk_color),
            ('resident_id', 'INT (FK)', fk_color),
            ('flat_id', 'INT (FK)', fk_color),
            ('title', 'VARCHAR', None),
            ('category', 'ENUM', None),
            ('description', 'TEXT', None),
            ('status', 'ENUM', None)
        ]),
        'VISITORS': (5.2, 0.2, 2.6, 2.2, [
            ('id', 'INT (PK)', pk_color),
            ('flat_id', 'INT (FK)', fk_color),
            ('visitor_name', 'VARCHAR', None),
            ('phone', 'VARCHAR', None),
            ('entry_time', 'DATETIME', None),
            ('status', 'ENUM', None)
        ])
    }

    for name, (x, y, w, h, attrs) in entities.items():
        # Header Box
        header_rect = patches.FancyBboxPatch((x, y + h - 0.5), w, 0.5, boxstyle="square,pad=0",
                                             facecolor=border_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(header_rect)
        ax.text(x + w/2, y + h - 0.25, name, color='white', weight='bold', fontsize=11, ha='center', va='center')

        # Body Box
        body_rect = patches.FancyBboxPatch((x, y), w, h - 0.5, boxstyle="square,pad=0",
                                           facecolor=box_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(body_rect)

        # Attributes text
        line_y = y + h - 0.8
        for attr_name, attr_type, color in attrs:
            t_color = color if color else '#1F2937'
            weight = 'bold' if color else 'normal'
            ax.text(x + 0.15, line_y, attr_name, color=t_color, fontsize=8.5, weight=weight, va='center')
            ax.text(x + w - 0.15, line_y, attr_type, color='#6B7280', fontsize=8, ha='right', va='center')
            line_y -= 0.32

    # Draw Relationship Connectors
    # Flats to Residents (1:N)
    ax.annotate('', xy=(9.5, 8.2), xytext=(7.8, 8.2),
                arrowprops=dict(arrowstyle="-|>", color='#1E3A8A', lw=1.8))
    ax.text(8.65, 8.35, '1 : N\nhouses', ha='center', fontsize=8, weight='bold', color='#1E3A8A')

    # Users to Residents (1:1)
    ax.annotate('', xy=(3.5, 8.2), xytext=(5.2, 8.2),
                arrowprops=dict(arrowstyle="<|-|>", color='#1E3A8A', lw=1.8))
    ax.text(4.35, 8.35, '1 : 1\nlogin', ha='center', fontsize=8, weight='bold', color='#1E3A8A')

    # Flats to Maintenance (1:N)
    ax.annotate('', xy=(2.3, 5.8), xytext=(5.2, 7.2),
                arrowprops=dict(arrowstyle="-|>", color='#1E3A8A', lw=1.8))
    ax.text(3.5, 6.6, '1 : N (bills)', ha='center', fontsize=8, weight='bold', color='#1E3A8A')

    # Maintenance to Payments (1:1)
    ax.annotate('', xy=(5.2, 4.2), xytext=(3.6, 4.2),
                arrowprops=dict(arrowstyle="-|>", color='#1E3A8A', lw=1.8))
    ax.text(4.4, 4.35, '1 : 1 (settles)', ha='center', fontsize=8, weight='bold', color='#1E3A8A')

    # Residents to Complaints (1:N)
    ax.annotate('', xy=(10.8, 5.8), xytext=(10.8, 6.8),
                arrowprops=dict(arrowstyle="-|>", color='#1E3A8A', lw=1.8))
    ax.text(11.3, 6.3, '1 : N\nlogs', ha='center', fontsize=8, weight='bold', color='#1E3A8A')

    # Flats to Visitors (1:N)
    ax.annotate('', xy=(6.5, 2.4), xytext=(6.5, 2.8),
                arrowprops=dict(arrowstyle="-|>", color='#1E3A8A', lw=1.8))
    ax.text(7.2, 2.5, '1 : N (visits)', ha='center', fontsize=8, weight='bold', color='#1E3A8A')

    plt.tight_layout()
    plt.savefig('report_assets/diagrams/fig01_er_diagram.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("✓ Created fig01_er_diagram.png")

# -------------------------------------------------------------------
# Figure 2: DFD Level 0 (Context Diagram)
# -------------------------------------------------------------------
def generate_dfd_level0():
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # Central Process: 0.0 Society Management System
    center_circle = patches.Circle((5, 3.5), 1.35, facecolor='#1E3A8A', edgecolor='#0F172A', lw=2)
    ax.add_patch(center_circle)
    ax.text(5, 3.65, '0.0\nHousing Society', color='white', weight='bold', fontsize=11, ha='center', va='center')
    ax.text(5, 3.25, 'Management\nSystem', color='#93C5FD', weight='bold', fontsize=9.5, ha='center', va='center')

    # External Entities
    # Admin (Left)
    admin_box = patches.Rectangle((0.5, 2.6), 1.8, 1.8, facecolor='#E2E8F0', edgecolor='#1E3A8A', lw=2)
    ax.add_patch(admin_box)
    ax.text(1.4, 3.5, 'ADMIN\n(Secretary)', color='#0F172A', weight='bold', fontsize=10, ha='center', va='center')

    # Resident (Top Right)
    res_box = patches.Rectangle((7.7, 4.4), 1.8, 1.8, facecolor='#E2E8F0', edgecolor='#1E3A8A', lw=2)
    ax.add_patch(res_box)
    ax.text(8.6, 5.3, 'RESIDENT\n(Flat Owner)', color='#0F172A', weight='bold', fontsize=10, ha='center', va='center')

    # Security Guard (Bottom Right)
    sec_box = patches.Rectangle((7.7, 0.8), 1.8, 1.8, facecolor='#E2E8F0', edgecolor='#1E3A8A', lw=2)
    ax.add_patch(sec_box)
    ax.text(8.6, 1.7, 'SECURITY\n(Main Gate)', color='#0F172A', weight='bold', fontsize=10, ha='center', va='center')

    # Arrows Admin <-> System
    ax.annotate('', xy=(3.65, 4.1), xytext=(2.3, 4.1),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.5))
    ax.text(2.95, 4.25, 'Flats, Bills, Notices', fontsize=7.5, ha='center', weight='bold', color='#1E3A8A')

    ax.annotate('', xy=(2.3, 2.9), xytext=(3.65, 2.9),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.5))
    ax.text(2.95, 2.65, 'Reports, Audit Logs', fontsize=7.5, ha='center', weight='bold', color='#1E3A8A')

    # Arrows Resident <-> System
    ax.annotate('', xy=(6.2, 4.3), xytext=(7.7, 5.0),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.5))
    ax.text(6.8, 4.9, 'Complaints, Payments', fontsize=7.5, ha='center', weight='bold', color='#1E3A8A', rotation=-22)

    ax.annotate('', xy=(7.7, 4.6), xytext=(6.3, 3.9),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.5))
    ax.text(7.2, 4.0, 'Receipts, Notices', fontsize=7.5, ha='center', weight='bold', color='#1E3A8A', rotation=-22)

    # Arrows Security <-> System
    ax.annotate('', xy=(6.2, 2.7), xytext=(7.7, 2.0),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.5))
    ax.text(6.8, 2.1, 'Visitor Check-in/Exit', fontsize=7.5, ha='center', weight='bold', color='#1E3A8A', rotation=22)

    ax.annotate('', xy=(7.7, 2.4), xytext=(6.3, 3.1),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.5))
    ax.text(7.2, 3.0, 'Flat Verification', fontsize=7.5, ha='center', weight='bold', color='#1E3A8A', rotation=22)

    plt.tight_layout()
    plt.savefig('report_assets/diagrams/fig02_dfd_level0.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("✓ Created fig02_dfd_level0.png")

# -------------------------------------------------------------------
# Figure 3: DFD Level 1
# -------------------------------------------------------------------
def generate_dfd_level1():
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Processes
    processes = [
        (2.0, 6.0, '1.0\nAuthentication\n& Session'),
        (6.0, 6.0, '2.0\nFlat & Resident\nManagement'),
        (10.0, 6.0, '3.0\nMaintenance &\nPayment Billing'),
        (2.0, 2.0, '4.0\nComplaints &\nGrievance Mgmt'),
        (6.0, 2.0, '5.0\nSecurity Gate\nVisitor Tracking'),
        (10.0, 2.0, '6.0\nNotice Board &\nReporting')
    ]

    for x, y, label in processes:
        p_circle = patches.Circle((x, y), 0.95, facecolor='#1E3A8A', edgecolor='#0F172A', lw=1.8)
        ax.add_patch(p_circle)
        ax.text(x, y, label, color='white', weight='bold', fontsize=8.5, ha='center', va='center')

    # Data Stores (Open-ended rectangles)
    stores = [
        (4.5, 4.2, 'D1: USERS & RESIDENTS'),
        (8.5, 4.2, 'D2: MAINTENANCE & PAYMENTS'),
        (4.5, 0.5, 'D3: COMPLAINTS & NOTICES'),
        (8.5, 0.5, 'D4: VISITORS LOG')
    ]

    for x, y, label in stores:
        # Top and bottom line for data store
        ax.plot([x - 1.3, x + 1.3], [y + 0.3, y + 0.3], color='#1E3A8A', lw=2)
        ax.plot([x - 1.3, x + 1.3], [y - 0.3, y - 0.3], color='#1E3A8A', lw=2)
        ax.plot([x - 1.3, x - 1.3], [y - 0.3, y + 0.3], color='#1E3A8A', lw=2)
        ax.fill_between([x - 1.3, x + 1.3], y - 0.3, y + 0.3, facecolor='#F1F5F9')
        ax.text(x, y, label, color='#0F172A', weight='bold', fontsize=7.5, ha='center', va='center')

    # Connectors
    # Process 1.0 to D1
    ax.annotate('', xy=(3.8, 4.5), xytext=(2.6, 5.3),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.4))
    # Process 2.0 to D1
    ax.annotate('', xy=(5.2, 4.5), xytext=(5.6, 5.2),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.4))
    # Process 3.0 to D2
    ax.annotate('', xy=(9.2, 4.5), xytext=(9.6, 5.2),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.4))
    # Process 4.0 to D3
    ax.annotate('', xy=(4.0, 0.8), xytext=(2.6, 1.3),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.4))
    # Process 5.0 to D4
    ax.annotate('', xy=(8.0, 0.8), xytext=(6.6, 1.3),
                arrowprops=dict(arrowstyle="->", color='#1E3A8A', lw=1.4))

    plt.tight_layout()
    plt.savefig('report_assets/diagrams/fig03_dfd_level1.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("✓ Created fig03_dfd_level1.png")

# -------------------------------------------------------------------
# Figure 4: Use Case Diagram
# -------------------------------------------------------------------
def generate_usecase():
    fig, ax = plt.subplots(figsize=(11, 8), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # System boundary box
    sys_box = patches.Rectangle((2.8, 0.4), 5.4, 8.2, facecolor='#FAFAFA', edgecolor='#1E3A8A', lw=2, linestyle='--')
    ax.add_patch(sys_box)
    ax.text(5.5, 8.35, 'Housing Society Management Portal', color='#1E3A8A', weight='bold', fontsize=11, ha='center')

    # Actors
    def draw_actor(x, y, label):
        ax.plot([x, x], [y - 0.4, y - 0.9], color='#0F172A', lw=2) # body
        head = patches.Circle((x, y - 0.2), 0.2, facecolor='#E2E8F0', edgecolor='#0F172A', lw=2)
        ax.add_patch(head)
        ax.plot([x - 0.35, x + 0.35], [y - 0.55, y - 0.55], color='#0F172A', lw=2) # arms
        ax.plot([x, x - 0.25], [y - 0.9, y - 1.3], color='#0F172A', lw=2) # left leg
        ax.plot([x, x + 0.25], [y - 0.9, y - 1.3], color='#0F172A', lw=2) # right leg
        ax.text(x, y - 1.55, label, color='#0F172A', weight='bold', fontsize=9.5, ha='center')

    draw_actor(1.2, 7.2, 'Admin\n(Secretary)')
    draw_actor(9.8, 7.2, 'Resident\n(Flat Owner)')
    draw_actor(9.8, 2.8, 'Security\n(Gate Guard)')

    # Use Cases (Ellipses)
    usecases = [
        (5.5, 7.6, 'Manage Flats & Residents'),
        (5.5, 6.7, 'Generate Maintenance Bills'),
        (5.5, 5.8, 'View Bills & Pay Dues'),
        (5.5, 4.9, 'Lodge / Resolve Complaints'),
        (5.5, 4.0, 'Publish & Read Notices'),
        (5.5, 3.1, 'Check-in Visitors & Mark Exit'),
        (5.5, 2.2, 'Manage Vehicles & Parking'),
        (5.5, 1.3, 'Download Audit Reports & CSV')
    ]

    for x, y, label in usecases:
        ellipse = patches.Ellipse((x, y), 3.8, 0.65, facecolor='#EFF6FF', edgecolor='#1E3A8A', lw=1.5)
        ax.add_patch(ellipse)
        ax.text(x, y, label, color='#1E3A8A', weight='bold', fontsize=8.5, ha='center', va='center')

    # Connections Admin
    ax.plot([1.5, 3.6], [6.2, 7.6], color='#64748B', lw=1.2)
    ax.plot([1.5, 3.6], [6.2, 6.7], color='#64748B', lw=1.2)
    ax.plot([1.5, 3.6], [6.2, 4.9], color='#64748B', lw=1.2)
    ax.plot([1.5, 3.6], [6.2, 4.0], color='#64748B', lw=1.2)
    ax.plot([1.5, 3.6], [6.2, 2.2], color='#64748B', lw=1.2)
    ax.plot([1.5, 3.6], [6.2, 1.3], color='#64748B', lw=1.2)

    # Connections Resident
    ax.plot([9.5, 7.4], [6.2, 5.8], color='#64748B', lw=1.2)
    ax.plot([9.5, 7.4], [6.2, 4.9], color='#64748B', lw=1.2)
    ax.plot([9.5, 7.4], [6.2, 4.0], color='#64748B', lw=1.2)

    # Connections Security
    ax.plot([9.5, 7.4], [2.0, 3.1], color='#64748B', lw=1.2)

    plt.tight_layout()
    plt.savefig('report_assets/diagrams/fig04_use_case.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("✓ Created fig04_use_case.png")

# -------------------------------------------------------------------
# Figure 5: System Architecture (Three-Tier Architecture)
# -------------------------------------------------------------------
def generate_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8)
    ax.axis('off')

    tiers = [
        ('PRESENTATION LAYER (Client Browser)', 5.5, 6.5, 9.0, 1.5, '#EFF6FF', '#1E3A8A', [
            'HTML5 / CSS3 Responsive Layout', 'Bootstrap 5 Framework', 'Jinja2 Dynamic Templates', 'Interactive Client Scripts'
        ]),
        ('APPLICATION LAYER (Flask Web Server)', 5.5, 4.0, 9.0, 1.8, '#F0FDF4', '#15803D', [
            'Flask WSGI Microframework', 'Authentication & Session Middleware', 'Role-Based Access Controller', 'Billing & Reporting Logic Engine'
        ]),
        ('DATA LAYER (Storage & Database)', 5.5, 1.4, 9.0, 1.6, '#FFFBEB', '#B45309', [
            'SQLite / MySQL Relational Database Engine', 'ACID Transactions & Foreign Key Integrity', 'Normalized Relational Tables', 'Daily Backup & Audit Trail Storage'
        ])
    ]

    for title, cx, cy, w, h, bg, border, items in tiers:
        rect = patches.FancyBboxPatch((cx - w/2, cy - h/2), w, h, boxstyle="round,pad=0.2",
                                      facecolor=bg, edgecolor=border, lw=2)
        ax.add_patch(rect)
        ax.text(cx, cy + h/2 - 0.3, title, color=border, weight='bold', fontsize=10.5, ha='center')

        # Sub-boxes for items
        col_w = w / 2 - 0.4
        for idx, it in enumerate(items):
            ix = cx - w/2 + 0.3 + (idx % 2) * (col_w + 0.4)
            iy = cy - 0.4 + (1 - idx // 2) * 0.5
            s_rect = patches.Rectangle((ix, iy), col_w, 0.38, facecolor='white', edgecolor='#CBD5E1', lw=1)
            ax.add_patch(s_rect)
            ax.text(ix + col_w/2, iy + 0.19, it, color='#1F2937', fontsize=8, ha='center', va='center')

    # Connectors between tiers
    ax.annotate('', xy=(4.2, 5.0), xytext=(4.2, 5.6),
                arrowprops=dict(arrowstyle="<->", color='#1E3A8A', lw=2))
    ax.text(4.7, 5.3, 'HTTP Requests / JSON / HTML', fontsize=8, weight='bold', color='#1E3A8A', va='center')

    ax.annotate('', xy=(4.2, 2.3), xytext=(4.2, 3.0),
                arrowprops=dict(arrowstyle="<->", color='#15803D', lw=2))
    ax.text(4.7, 2.65, 'SQL Queries / Parameterized Cursors', fontsize=8, weight='bold', color='#15803D', va='center')

    plt.tight_layout()
    plt.savefig('report_assets/diagrams/fig05_system_architecture.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("✓ Created fig05_system_architecture.png")

# -------------------------------------------------------------------
# Figure 6: Flowchart (Complaint & Visitor Lifecycle)
# -------------------------------------------------------------------
def generate_flowchart():
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Flowchart: Complaint Lodging & Maintenance Lifecycle
    def draw_box(x, y, w, h, text, shape='rect', bg='#EFF6FF', border='#1E3A8A'):
        if shape == 'round':
            p = patches.FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.2", facecolor=bg, edgecolor=border, lw=2)
        elif shape == 'diamond':
            pts = [[x, y + h/2], [x + w/2, y], [x, y - h/2], [x - w/2, y]]
            p = patches.Polygon(pts, facecolor=bg, edgecolor=border, lw=2)
        else:
            p = patches.Rectangle((x - w/2, y - h/2), w, h, facecolor=bg, edgecolor=border, lw=2)
        ax.add_patch(p)
        ax.text(x, y, text, color='#0F172A', weight='bold', fontsize=8.5, ha='center', va='center')

    # Start
    draw_box(5.5, 9.4, 2.6, 0.6, 'START', shape='round', bg='#DCFCE7', border='#15803D')

    # Step 1: User Login
    draw_box(5.5, 8.3, 3.4, 0.7, 'User Enters Credentials\n(admin / resident / security)')
    ax.annotate('', xy=(5.5, 8.65), xytext=(5.5, 9.1), arrowprops=dict(arrowstyle="->", lw=1.5))

    # Step 2: Role Decision
    draw_box(5.5, 6.9, 3.4, 1.1, 'Verify Role &\nSession Valid?', shape='diamond', bg='#FEF3C7', border='#D97706')
    ax.annotate('', xy=(5.5, 7.45), xytext=(5.5, 7.95), arrowprops=dict(arrowstyle="->", lw=1.5))

    # Left: Resident Workflow
    draw_box(2.2, 5.3, 3.0, 0.8, 'Resident Dashboard:\nView Dues / Lodge Complaint')
    ax.annotate('', xy=(2.2, 5.7), xytext=(4.0, 6.9), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(2.8, 6.5, 'Resident', fontsize=8, weight='bold', color='#1E3A8A')

    # Center: Admin Workflow
    draw_box(5.5, 5.3, 2.8, 0.8, 'Admin Dashboard:\nBilling, Flats, Notices')
    ax.annotate('', xy=(5.5, 5.7), xytext=(5.5, 6.35), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(5.8, 6.0, 'Admin', fontsize=8, weight='bold', color='#1E3A8A')

    # Right: Security Workflow
    draw_box(8.8, 5.3, 3.0, 0.8, 'Security Gate Console:\nVisitor Entry & Exit Pass')
    ax.annotate('', xy=(8.8, 5.7), xytext=(7.0, 6.9), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(8.1, 6.5, 'Security', fontsize=8, weight='bold', color='#1E3A8A')

    # Actions
    draw_box(2.2, 3.8, 3.0, 0.8, 'Pay Bill via UPI\nAuto-Generate Receipt')
    ax.annotate('', xy=(2.2, 4.2), xytext=(2.2, 4.9), arrowprops=dict(arrowstyle="->", lw=1.5))

    draw_box(5.5, 3.8, 2.8, 0.8, 'Assign Contractor &\nMark Status RESOLVED')
    ax.annotate('', xy=(5.5, 4.2), xytext=(5.5, 4.9), arrowprops=dict(arrowstyle="->", lw=1.5))

    draw_box(8.8, 3.8, 3.0, 0.8, '1-Click Exit Marking\nRecord Exit Timestamp')
    ax.annotate('', xy=(8.8, 4.2), xytext=(8.8, 4.9), arrowprops=dict(arrowstyle="->", lw=1.5))

    # Convergence to Database
    draw_box(5.5, 2.2, 5.4, 0.8, 'Commit Transactions to Database\n& Update Status Logs')
    ax.annotate('', xy=(4.0, 2.6), xytext=(2.2, 3.4), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate('', xy=(5.5, 2.6), xytext=(5.5, 3.4), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate('', xy=(7.0, 2.6), xytext=(8.8, 3.4), arrowprops=dict(arrowstyle="->", lw=1.5))

    # End
    draw_box(5.5, 0.9, 2.6, 0.6, 'END', shape='round', bg='#FEE2E2', border='#DC2626')
    ax.annotate('', xy=(5.5, 1.2), xytext=(5.5, 1.8), arrowprops=dict(arrowstyle="->", lw=1.5))

    plt.tight_layout()
    plt.savefig('report_assets/diagrams/fig06_flowchart.png', bbox_inches='tight', dpi=300)
    plt.close()
    print("✓ Created fig06_flowchart.png")

if __name__ == '__main__':
    generate_er_diagram()
    generate_dfd_level0()
    generate_dfd_level1()
    generate_usecase()
    generate_architecture()
    generate_flowchart()
    print("All 6 diagrams generated successfully!")
