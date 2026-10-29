import os
import csv
import io
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from config import Config
from db import query_db, execute_db, check_db_status, init_database

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database is created and seeded
init_database()

# -------------------------------------------------------------
# Context Processor & Decorators
# -------------------------------------------------------------
@app.context_processor
def inject_globals():
    return {
        'current_date': date.today().strftime('%d %B %Y')
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                flash('Please log in first.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                flash('Access denied. You do not have permission for this section.', 'danger')
                if session.get('role') == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif session.get('role') == 'resident':
                    return redirect(url_for('resident_dashboard'))
                elif session.get('role') == 'security':
                    return redirect(url_for('security_dashboard'))
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------------------------------------------------
# Authentication Routes
# -------------------------------------------------------------
@app.route('/')
def index():
    if session.get('user_id'):
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'resident':
            return redirect(url_for('resident_dashboard'))
        elif role == 'security':
            return redirect(url_for('security_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']

            flash(f"Welcome back, {user['full_name']}!", 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'resident':
                return redirect(url_for('resident_dashboard'))
            elif user['role'] == 'security':
                return redirect(url_for('security_dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# -------------------------------------------------------------
# Admin Dashboard & Modules
# -------------------------------------------------------------
@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    # Gather KPI stats
    total_flats = query_db("SELECT COUNT(*) as cnt FROM flats", one=True)['cnt']
    occupied_flats = query_db("SELECT COUNT(*) as cnt FROM flats WHERE status = 'Occupied'", one=True)['cnt']
    vacant_flats = total_flats - occupied_flats
    total_residents = query_db("SELECT COUNT(*) as cnt FROM residents WHERE status = 'Active'", one=True)['cnt']

    pending_dues_row = query_db("SELECT SUM(total_amount) as total FROM maintenance WHERE status = 'PENDING'", one=True)
    pending_dues = pending_dues_row['total'] or 0.0

    paid_row = query_db("SELECT SUM(amount_paid) as total FROM payments", one=True)
    paid_amount = paid_row['total'] or 0.0

    open_complaints = query_db("SELECT COUNT(*) as cnt FROM complaints WHERE status IN ('OPEN', 'IN PROGRESS')", one=True)['cnt']
    visitors_inside = query_db("SELECT COUNT(*) as cnt FROM visitors WHERE status = 'Inside'", one=True)['cnt']

    stats = {
        'total_flats': total_flats,
        'occupied_flats': occupied_flats,
        'vacant_flats': vacant_flats,
        'total_residents': total_residents,
        'pending_dues': pending_dues,
        'paid_amount': paid_amount,
        'open_complaints': open_complaints,
        'visitors_inside': visitors_inside
    }

    # Recent items
    recent_complaints = query_db('''
        SELECT c.*, f.flat_number, r.name as resident_name
        FROM complaints c
        JOIN flats f ON c.flat_id = f.id
        LEFT JOIN residents r ON c.resident_id = r.id
        ORDER BY c.id DESC LIMIT 5
    ''')

    active_visitors = query_db('''
        SELECT v.*, f.flat_number
        FROM visitors v
        JOIN flats f ON v.flat_id = f.id
        WHERE v.status = 'Inside'
        ORDER BY v.id DESC LIMIT 5
    ''')

    recent_payments = query_db('''
        SELECT p.*, f.flat_number, m.month_year
        FROM payments p
        JOIN flats f ON p.flat_id = f.id
        JOIN maintenance m ON p.maintenance_id = m.id
        ORDER BY p.id DESC LIMIT 5
    ''')

    return render_template('admin_dashboard.html',
                           active_page='admin_dashboard',
                           stats=stats,
                           recent_complaints=recent_complaints,
                           active_visitors=active_visitors,
                           recent_payments=recent_payments)

# --- Flat Management ---
@app.route('/admin/flats')
@role_required('admin')
def flats():
    all_flats = query_db("SELECT * FROM flats ORDER BY wing ASC, floor ASC, flat_number ASC")
    return render_template('flats.html', active_page='flats', flats=all_flats)

@app.route('/admin/flats/add', methods=['POST'])
@role_required('admin')
def add_flat():
    flat_number = request.form.get('flat_number', '').strip().upper()
    wing = request.form.get('wing', '').strip().upper()
    floor = int(request.form.get('floor', 1))
    flat_type = request.form.get('flat_type', '2BHK')
    owner_name = request.form.get('owner_name', '').strip()
    owner_phone = request.form.get('owner_phone', '').strip()
    status = request.form.get('status', 'Vacant')

    try:
        execute_db('''
            INSERT INTO flats (flat_number, wing, floor, flat_type, owner_name, owner_phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (flat_number, wing, floor, flat_type, owner_name, owner_phone, status))
        flash(f"Flat {flat_number} added successfully.", 'success')
    except Exception as e:
        flash(f"Error adding flat: {e}", 'danger')

    return redirect(url_for('flats'))

@app.route('/admin/flats/edit/<int:flat_id>', methods=['POST'])
@role_required('admin')
def edit_flat(flat_id):
    wing = request.form.get('wing', '').strip().upper()
    floor = int(request.form.get('floor', 1))
    flat_type = request.form.get('flat_type', '2BHK')
    owner_name = request.form.get('owner_name', '').strip()
    owner_phone = request.form.get('owner_phone', '').strip()
    resident_name = request.form.get('resident_name', '').strip() or None
    resident_phone = request.form.get('resident_phone', '').strip() or None
    status = request.form.get('status', 'Vacant')

    execute_db('''
        UPDATE flats
        SET wing = ?, floor = ?, flat_type = ?, owner_name = ?, owner_phone = ?,
            resident_name = ?, resident_phone = ?, status = ?
        WHERE id = ?
    ''', (wing, floor, flat_type, owner_name, owner_phone, resident_name, resident_phone, status, flat_id))

    flash("Flat details updated successfully.", 'success')
    return redirect(url_for('flats'))

@app.route('/admin/flats/delete/<int:flat_id>', methods=['POST'])
@role_required('admin')
def delete_flat(flat_id):
    execute_db("DELETE FROM flats WHERE id = ?", (flat_id,))
    flash("Flat deleted successfully.", 'info')
    return redirect(url_for('flats'))

# --- Resident Management ---
@app.route('/admin/residents')
@role_required('admin')
def residents():
    resident_list = query_db('''
        SELECT r.*, f.flat_number, f.wing
        FROM residents r
        JOIN flats f ON r.flat_id = f.id
        ORDER BY f.flat_number ASC
    ''')
    all_flats = query_db("SELECT id, flat_number, wing, floor FROM flats ORDER BY flat_number ASC")
    return render_template('residents.html', active_page='residents', residents=resident_list, flats=all_flats)

@app.route('/admin/residents/add', methods=['POST'])
@role_required('admin')
def add_resident():
    flat_id = int(request.form.get('flat_id'))
    name = request.form.get('name', '').strip()
    mobile = request.form.get('mobile', '').strip()
    email = request.form.get('email', '').strip() or None
    resident_type = request.form.get('resident_type', 'Owner')
    family_members = int(request.form.get('family_members', 1))
    vehicle_number = request.form.get('vehicle_number', '').strip() or None

    execute_db('''
        INSERT INTO residents (flat_id, name, mobile, email, resident_type, family_members, vehicle_number, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')
    ''', (flat_id, name, mobile, email, resident_type, family_members, vehicle_number))

    # Mark flat occupied and set resident info
    execute_db('''
        UPDATE flats
        SET status = 'Occupied', resident_name = ?, resident_phone = ?
        WHERE id = ?
    ''', (name, mobile, flat_id))

    flash(f"Resident {name} registered successfully.", 'success')
    return redirect(url_for('residents'))

@app.route('/admin/residents/delete/<int:resident_id>', methods=['POST'])
@role_required('admin')
def delete_resident(resident_id):
    res = query_db("SELECT flat_id FROM residents WHERE id = ?", (resident_id,), one=True)
    if res:
        execute_db("DELETE FROM residents WHERE id = ?", (resident_id,))
        # Check if flat has remaining residents
        rem = query_db("SELECT COUNT(*) as cnt FROM residents WHERE flat_id = ?", (res['flat_id'],), one=True)['cnt']
        if rem == 0:
            execute_db("UPDATE flats SET status = 'Vacant', resident_name = NULL, resident_phone = NULL WHERE id = ?", (res['flat_id'],))
    flash("Resident record removed.", 'info')
    return redirect(url_for('residents'))

# --- Maintenance & Payments ---
@app.route('/admin/maintenance')
@role_required('admin')
def maintenance():
    maint_list = query_db('''
        SELECT m.*, f.flat_number, f.owner_name, p.id as payment_id
        FROM maintenance m
        JOIN flats f ON m.flat_id = f.id
        LEFT JOIN payments p ON m.id = p.maintenance_id
        ORDER BY m.id DESC
    ''')
    occupied_flats = query_db("SELECT id, flat_number, owner_name FROM flats WHERE status = 'Occupied' ORDER BY flat_number ASC")

    total_billed = query_db("SELECT SUM(total_amount) as total FROM maintenance", one=True)['total'] or 0.0
    total_paid = query_db("SELECT SUM(amount_paid) as total FROM payments", one=True)['total'] or 0.0
    total_pending = query_db("SELECT SUM(total_amount) as total FROM maintenance WHERE status = 'PENDING'", one=True)['total'] or 0.0

    return render_template('maintenance.html',
                           active_page='maintenance',
                           maintenance_list=maint_list,
                           flats=occupied_flats,
                           total_billed=total_billed,
                           total_paid=total_paid,
                           total_pending=total_pending)

@app.route('/admin/maintenance/generate', methods=['POST'])
@role_required('admin')
def generate_bill():
    target = request.form.get('flat_id')
    month_year = request.form.get('month_year', '').strip()
    due_date = request.form.get('due_date', '')
    m_amt = float(request.form.get('maintenance_amount', 3000.0))
    p_amt = float(request.form.get('parking_amount', 500.0))
    o_amt = float(request.form.get('other_amount', 200.0))
    total_amt = m_amt + p_amt + o_amt

    if target == 'ALL':
        occupied_flats = query_db("SELECT id FROM flats WHERE status = 'Occupied'")
        for f in occupied_flats:
            execute_db('''
                INSERT INTO maintenance (flat_id, month_year, maintenance_amount, parking_amount, other_amount, total_amount, status, due_date)
                VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
            ''', (f['id'], month_year, m_amt, p_amt, o_amt, total_amt, due_date))
        flash(f"Maintenance bills for '{month_year}' generated for {len(occupied_flats)} occupied flats.", 'success')
    else:
        flat_id = int(target)
        execute_db('''
            INSERT INTO maintenance (flat_id, month_year, maintenance_amount, parking_amount, other_amount, total_amount, status, due_date)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
        ''', (flat_id, month_year, m_amt, p_amt, o_amt, total_amt, due_date))
        flash(f"Maintenance bill for '{month_year}' generated.", 'success')

    return redirect(url_for('maintenance'))

@app.route('/admin/maintenance/pay', methods=['POST'])
@role_required('admin')
def record_payment():
    maint_id = int(request.form.get('maintenance_id'))
    flat_id = int(request.form.get('flat_id'))
    amount = float(request.form.get('amount_paid'))
    payment_mode = request.form.get('payment_mode', 'UPI')
    reference_no = request.form.get('reference_no', '').strip() or None
    receipt_no = f"REC-{datetime.now().strftime('%Y%m')}-{maint_id:04d}"

    payment_id = execute_db('''
        INSERT INTO payments (maintenance_id, flat_id, amount_paid, payment_mode, reference_no, receipt_no)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (maint_id, flat_id, amount, payment_mode, reference_no, receipt_no))

    execute_db("UPDATE maintenance SET status = 'PAID' WHERE id = ?", (maint_id,))

    flash(f"Payment of ₹{amount:,.2f} recorded. Receipt {receipt_no} generated.", 'success')
    return redirect(url_for('view_receipt', payment_id=payment_id))

@app.route('/receipt/<int:payment_id>')
@login_required
def view_receipt(payment_id):
    payment = query_db('''
        SELECT p.*, f.flat_number, f.wing, f.floor, f.owner_name,
               m.month_year, m.maintenance_amount, m.parking_amount, m.other_amount
        FROM payments p
        JOIN flats f ON p.flat_id = f.id
        JOIN maintenance m ON p.maintenance_id = m.id
        WHERE p.id = ?
    ''', (payment_id,), one=True)

    if not payment:
        flash("Payment receipt not found.", 'danger')
        return redirect(url_for('maintenance'))

    return render_template('receipt.html', payment=payment)

# --- Complaints Management ---
@app.route('/admin/complaints')
@role_required('admin')
def complaints():
    all_complaints = query_db('''
        SELECT c.*, f.flat_number, r.name as resident_name
        FROM complaints c
        JOIN flats f ON c.flat_id = f.id
        LEFT JOIN residents r ON c.resident_id = r.id
        ORDER BY c.id DESC
    ''')
    return render_template('complaints.html', active_page='complaints', complaints=all_complaints)

@app.route('/admin/complaints/update/<int:complaint_id>', methods=['POST'])
@role_required('admin')
def update_complaint(complaint_id):
    status = request.form.get('status')
    assigned_to = request.form.get('assigned_to', '').strip() or None
    admin_response = request.form.get('admin_response', '').strip() or None

    execute_db('''
        UPDATE complaints
        SET status = ?, assigned_to = ?, admin_response = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, assigned_to, admin_response, complaint_id))

    flash(f"Complaint #C-{complaint_id} updated.", 'success')
    return redirect(url_for('complaints'))

# --- Visitors Management ---
@app.route('/admin/visitors')
@role_required('admin', 'security')
def visitors():
    active_visitors = query_db('''
        SELECT v.*, f.flat_number
        FROM visitors v
        JOIN flats f ON v.flat_id = f.id
        WHERE v.status = 'Inside'
        ORDER BY v.id DESC
    ''')
    history = query_db('''
        SELECT v.*, f.flat_number
        FROM visitors v
        JOIN flats f ON v.flat_id = f.id
        ORDER BY v.id DESC
    ''')
    all_flats = query_db("SELECT id, flat_number, resident_name, owner_name FROM flats ORDER BY flat_number ASC")
    return render_template('visitors.html',
                           active_page='visitors',
                           active_visitors=active_visitors,
                           visitors_history=history,
                           flats=all_flats)

@app.route('/admin/visitors/add', methods=['POST'])
@role_required('admin', 'security')
def add_visitor():
    visitor_name = request.form.get('visitor_name', '').strip()
    phone = request.form.get('phone', '').strip()
    flat_id = int(request.form.get('flat_id'))
    purpose = request.form.get('purpose', 'Guest')
    vehicle_number = request.form.get('vehicle_number', '').strip() or None

    execute_db('''
        INSERT INTO visitors (visitor_name, phone, flat_id, purpose, vehicle_number, status, recorded_by)
        VALUES (?, ?, ?, ?, ?, 'Inside', ?)
    ''', (visitor_name, phone, flat_id, purpose, vehicle_number, session.get('user_id')))

    flash(f"Visitor {visitor_name} checked in successfully.", 'success')
    if session.get('role') == 'security':
        return redirect(url_for('security_dashboard'))
    return redirect(url_for('visitors'))

@app.route('/admin/visitors/exit/<int:visitor_id>', methods=['POST'])
@role_required('admin', 'security')
def visitor_exit(visitor_id):
    execute_db('''
        UPDATE visitors
        SET status = 'Exited', exit_time = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (visitor_id,))
    flash("Visitor exit recorded.", 'info')
    if session.get('role') == 'security':
        return redirect(url_for('security_dashboard'))
    return redirect(url_for('visitors'))

# --- Notices ---
@app.route('/notices')
@login_required
def notices():
    all_notices = query_db("SELECT * FROM notices WHERE is_active = 1 ORDER BY published_date DESC, id DESC")
    return render_template('notices.html', active_page='notices', notices=all_notices)

@app.route('/admin/notices/add', methods=['POST'])
@role_required('admin')
def add_notice():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'General')
    description = request.form.get('description', '').strip()

    execute_db('''
        INSERT INTO notices (title, category, description, published_date, created_by, is_active)
        VALUES (?, ?, ?, CURRENT_DATE, ?, 1)
    ''', (title, category, description, session.get('user_id')))

    flash("Society notice published successfully.", 'success')
    return redirect(url_for('notices'))

@app.route('/admin/notices/delete/<int:notice_id>', methods=['POST'])
@role_required('admin')
def delete_notice(notice_id):
    execute_db("DELETE FROM notices WHERE id = ?", (notice_id,))
    flash("Notice removed.", 'info')
    return redirect(url_for('notices'))

# --- Vehicles ---
@app.route('/admin/vehicles')
@role_required('admin')
def vehicles():
    all_vehicles = query_db('''
        SELECT v.*, f.flat_number
        FROM vehicles v
        JOIN flats f ON v.flat_id = f.id
        ORDER BY f.flat_number ASC
    ''')
    all_flats = query_db("SELECT id, flat_number, resident_name, owner_name FROM flats ORDER BY flat_number ASC")
    return render_template('vehicles.html', active_page='vehicles', vehicles=all_vehicles, flats=all_flats)

@app.route('/admin/vehicles/add', methods=['POST'])
@role_required('admin')
def add_vehicle():
    flat_id = int(request.form.get('flat_id'))
    vehicle_number = request.form.get('vehicle_number', '').strip().upper()
    vehicle_type = request.form.get('vehicle_type', 'Car')
    owner_name = request.form.get('owner_name', '').strip()

    try:
        execute_db('''
            INSERT INTO vehicles (flat_id, vehicle_number, vehicle_type, owner_name)
            VALUES (?, ?, ?, ?)
        ''', (flat_id, vehicle_number, vehicle_type, owner_name))
        flash(f"Vehicle {vehicle_number} registered successfully.", 'success')
    except Exception as e:
        flash(f"Error registering vehicle: {e}", 'danger')

    return redirect(url_for('vehicles'))

@app.route('/admin/vehicles/delete/<int:vehicle_id>', methods=['POST'])
@role_required('admin')
def delete_vehicle(vehicle_id):
    execute_db("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    flash("Vehicle record deleted.", 'info')
    return redirect(url_for('vehicles'))

# --- Reports & CSV Export ---
@app.route('/admin/reports')
@role_required('admin')
def reports():
    total_billed = query_db("SELECT SUM(total_amount) as total FROM maintenance", one=True)['total'] or 0.0
    total_paid = query_db("SELECT SUM(amount_paid) as total FROM payments", one=True)['total'] or 0.0
    total_pending = query_db("SELECT SUM(total_amount) as total FROM maintenance WHERE status = 'PENDING'", one=True)['total'] or 0.0

    return render_template('reports.html',
                           active_page='reports',
                           total_billed=total_billed,
                           total_paid=total_paid,
                           total_pending=total_pending)

@app.route('/admin/export/<report_type>')
@role_required('admin')
def export_csv(report_type):
    si = io.StringIO()
    writer = csv.writer(si)

    if report_type == 'residents':
        writer.writerow(['Flat Number', 'Resident Name', 'Mobile', 'Email', 'Type', 'Family Members', 'Vehicle Number', 'Status'])
        rows = query_db('''
            SELECT f.flat_number, r.name, r.mobile, r.email, r.resident_type, r.family_members, r.vehicle_number, r.status
            FROM residents r
            JOIN flats f ON r.flat_id = f.id
            ORDER BY f.flat_number ASC
        ''')
        for r in rows:
            writer.writerow([r['flat_number'], r['name'], r['mobile'], r['email'] or '', r['resident_type'], r['family_members'], r['vehicle_number'] or '', r['status']])
        filename = "Society_Residents_Report.csv"

    elif report_type == 'maintenance':
        writer.writerow(['Bill ID', 'Flat Number', 'Owner Name', 'Month/Year', 'Base Amount', 'Parking', 'Other', 'Total Amount', 'Due Date', 'Status'])
        rows = query_db('''
            SELECT m.id, f.flat_number, f.owner_name, m.month_year, m.maintenance_amount, m.parking_amount, m.other_amount, m.total_amount, m.due_date, m.status
            FROM maintenance m
            JOIN flats f ON m.flat_id = f.id
            ORDER BY m.id DESC
        ''')
        for r in rows:
            writer.writerow([r['id'], r['flat_number'], r['owner_name'], r['month_year'], r['maintenance_amount'], r['parking_amount'], r['other_amount'], r['total_amount'], r['due_date'] or '', r['status']])
        filename = "Society_Maintenance_Report.csv"

    elif report_type == 'complaints':
        writer.writerow(['Complaint ID', 'Flat Number', 'Resident Name', 'Category', 'Title', 'Description', 'Status', 'Assigned To', 'Admin Response', 'Date'])
        rows = query_db('''
            SELECT c.id, f.flat_number, r.name, c.category, c.title, c.description, c.status, c.assigned_to, c.admin_response, c.created_at
            FROM complaints c
            JOIN flats f ON c.flat_id = f.id
            LEFT JOIN residents r ON c.resident_id = r.id
            ORDER BY c.id DESC
        ''')
        for r in rows:
            writer.writerow([r['id'], r['flat_number'], r['name'], r['category'], r['title'], r['description'], r['status'], r['assigned_to'] or '', r['admin_response'] or '', r['created_at']])
        filename = "Society_Complaints_Report.csv"

    elif report_type == 'visitors':
        writer.writerow(['Log ID', 'Visitor Name', 'Phone', 'Flat Destination', 'Purpose', 'Vehicle Number', 'Entry Time', 'Exit Time', 'Status'])
        rows = query_db('''
            SELECT v.id, v.visitor_name, v.phone, f.flat_number, v.purpose, v.vehicle_number, v.entry_time, v.exit_time, v.status
            FROM visitors v
            JOIN flats f ON v.flat_id = f.id
            ORDER BY v.id DESC
        ''')
        for r in rows:
            writer.writerow([r['id'], r['visitor_name'], r['phone'], r['flat_number'], r['purpose'], r['vehicle_number'] or '', r['entry_time'], r['exit_time'] or '', r['status']])
        filename = "Society_Visitors_Report.csv"

    else:
        return "Invalid report type", 400

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output

# -------------------------------------------------------------
# Resident Portal Routes
# -------------------------------------------------------------
@app.route('/resident/dashboard')
@role_required('resident')
def resident_dashboard():
    # Resident Rahul Sharma has flat_id = 1
    resident = query_db("SELECT * FROM residents WHERE user_id = ?", (session.get('user_id'),), one=True)
    flat_id = resident['flat_id'] if resident else 1
    flat = query_db("SELECT * FROM flats WHERE id = ?", (flat_id,), one=True)

    pending_bill = query_db("SELECT * FROM maintenance WHERE flat_id = ? AND status = 'PENDING' ORDER BY id DESC LIMIT 1", (flat_id,), one=True)
    my_complaints = query_db("SELECT * FROM complaints WHERE flat_id = ? ORDER BY id DESC", (flat_id,))
    notices_list = query_db("SELECT * FROM notices WHERE is_active = 1 ORDER BY published_date DESC LIMIT 3")
    my_vehicles = query_db("SELECT * FROM vehicles WHERE flat_id = ?", (flat_id,))

    return render_template('resident_dashboard.html',
                           active_page='resident_dashboard',
                           flat=flat,
                           pending_bill=pending_bill,
                           my_complaints=my_complaints,
                           notices=notices_list,
                           my_vehicles=my_vehicles)

@app.route('/resident/bills')
@role_required('resident')
def resident_bills():
    resident = query_db("SELECT * FROM residents WHERE user_id = ?", (session.get('user_id'),), one=True)
    flat_id = resident['flat_id'] if resident else 1
    flat = query_db("SELECT * FROM flats WHERE id = ?", (flat_id,), one=True)

    bills = query_db('''
        SELECT m.*, p.id as payment_id
        FROM maintenance m
        LEFT JOIN payments p ON m.id = p.maintenance_id
        WHERE m.flat_id = ?
        ORDER BY m.id DESC
    ''', (flat_id,))

    return render_template('resident_bills.html', active_page='resident_bills', flat=flat, bills=bills)

@app.route('/resident/pay', methods=['POST'])
@role_required('resident')
def resident_pay():
    maint_id = int(request.form.get('maintenance_id'))
    amount = float(request.form.get('amount_paid'))
    payment_mode = request.form.get('payment_mode', 'UPI')
    reference_no = request.form.get('reference_no', '').strip() or f"UPI-{datetime.now().strftime('%H%M%S')}"

    resident = query_db("SELECT * FROM residents WHERE user_id = ?", (session.get('user_id'),), one=True)
    flat_id = resident['flat_id'] if resident else 1

    receipt_no = f"REC-{datetime.now().strftime('%Y%m')}-{maint_id:04d}"

    payment_id = execute_db('''
        INSERT INTO payments (maintenance_id, flat_id, amount_paid, payment_mode, reference_no, receipt_no)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (maint_id, flat_id, amount, payment_mode, reference_no, receipt_no))

    execute_db("UPDATE maintenance SET status = 'PAID' WHERE id = ?", (maint_id,))

    flash(f"Payment successful! Receipt {receipt_no} has been generated.", 'success')
    return redirect(url_for('view_receipt', payment_id=payment_id))

@app.route('/resident/complaints')
@role_required('resident')
def resident_complaints():
    resident = query_db("SELECT * FROM residents WHERE user_id = ?", (session.get('user_id'),), one=True)
    flat_id = resident['flat_id'] if resident else 1
    complaints_list = query_db("SELECT * FROM complaints WHERE flat_id = ? ORDER BY id DESC", (flat_id,))
    return render_template('resident_complaints.html', active_page='resident_complaints', my_complaints=complaints_list)

@app.route('/resident/complaints/submit', methods=['POST'])
@role_required('resident')
def resident_submit_complaint():
    resident = query_db("SELECT * FROM residents WHERE user_id = ?", (session.get('user_id'),), one=True)
    resident_id = resident['id'] if resident else 1
    flat_id = resident['flat_id'] if resident else 1

    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'Other')
    description = request.form.get('description', '').strip()

    execute_db('''
        INSERT INTO complaints (resident_id, flat_id, title, category, description, status)
        VALUES (?, ?, ?, ?, ?, 'OPEN')
    ''', (resident_id, flat_id, title, category, description))

    flash("Your complaint has been submitted to the society office.", 'success')
    return redirect(url_for('resident_complaints'))

# -------------------------------------------------------------
# Security Portal Routes
# -------------------------------------------------------------
@app.route('/security/dashboard')
@role_required('security')
def security_dashboard():
    active_visitors = query_db('''
        SELECT v.*, f.flat_number
        FROM visitors v
        JOIN flats f ON v.flat_id = f.id
        WHERE v.status = 'Inside'
        ORDER BY v.id DESC
    ''')
    all_flats = query_db("SELECT id, flat_number, wing, resident_name, owner_name FROM flats ORDER BY flat_number ASC")
    return render_template('security_dashboard.html',
                           active_page='security_dashboard',
                           active_visitors=active_visitors,
                           flats=all_flats)

@app.route('/security/visitors/add', methods=['POST'])
@role_required('security')
def security_add_visitor():
    visitor_name = request.form.get('visitor_name', '').strip()
    phone = request.form.get('phone', '').strip()
    flat_id = int(request.form.get('flat_id'))
    purpose = request.form.get('purpose', 'Guest')
    vehicle_number = request.form.get('vehicle_number', '').strip() or None

    execute_db('''
        INSERT INTO visitors (visitor_name, phone, flat_id, purpose, vehicle_number, status, recorded_by)
        VALUES (?, ?, ?, ?, ?, 'Inside', ?)
    ''', (visitor_name, phone, flat_id, purpose, vehicle_number, session.get('user_id')))

    flash(f"Gate pass issued for visitor '{visitor_name}'. Entry recorded.", 'success')
    return redirect(url_for('security_dashboard'))

@app.route('/security/visitors/exit/<int:visitor_id>', methods=['POST'])
@role_required('security')
def security_exit_visitor(visitor_id):
    execute_db('''
        UPDATE visitors
        SET status = 'Exited', exit_time = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (visitor_id,))
    flash("Visitor exit recorded at gate.", 'info')
    return redirect(url_for('security_dashboard'))

# -------------------------------------------------------------
# App Runner & Headless Preview Route
# -------------------------------------------------------------
@app.route('/dev-preview/<role>/<endpoint>')
def dev_preview(role, endpoint):
    user = query_db("SELECT * FROM users WHERE role = ?", (role,), one=True)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
    return redirect(url_for(endpoint))

if __name__ == '__main__':

    print("=" * 60)
    print("Central Park Housing Society Management System")
    print("Starting server on http://127.0.0.1:5001")
    print("Default Logins:")
    print("  • Admin:    admin / admin123")
    print("  • Resident: resident / resident123")
    print("  • Security: security / security123")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5001, debug=False)
