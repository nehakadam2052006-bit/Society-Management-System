import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

DB_FILE = os.path.join(os.path.dirname(__file__), 'database', 'society.db')

def get_connection():
    """
    Returns an SQLite connection configured with dict-like row access.
    """
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def query_db(query, args=(), one=False):
    """
    Executes a SELECT query and returns rows as dictionaries.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        cur.close()
        res = [dict(row) for row in rv]
        return (res[0] if res else None) if one else res
    finally:
        conn.close()

def execute_db(query, args=()):
    """
    Executes an INSERT, UPDATE, or DELETE query and returns the last inserted row id.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id
    finally:
        conn.close()

def check_db_status():
    """
    Checks database health and returns table names and counts.
    """
    status = {
        'connected': False,
        'db_exists': False,
        'tables': [],
        'error': None,
        'engine': 'SQLite',
        'db_file': DB_FILE,
        'counts': {}
    }
    try:
        if os.path.exists(DB_FILE):
            status['db_exists'] = True
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row['name'] for row in cur.fetchall()]
        status['tables'] = tables
        status['connected'] = True

        for t in tables:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {t}")
            status['counts'][t] = cur.fetchone()['cnt']
        cur.close()
        conn.close()
    except Exception as e:
        status['error'] = str(e)
    return status

def init_database(force=False):
    """
    Creates tables and seeds default test data.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Create tables
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'resident', 'security')),
        full_name TEXT NOT NULL,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS flats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flat_number TEXT NOT NULL UNIQUE,
        wing TEXT NOT NULL,
        floor INTEGER NOT NULL,
        flat_type TEXT DEFAULT '2BHK',
        owner_name TEXT NOT NULL,
        owner_phone TEXT NOT NULL,
        resident_name TEXT,
        resident_phone TEXT,
        status TEXT DEFAULT 'Vacant' CHECK(status IN ('Occupied', 'Vacant')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS residents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        flat_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        email TEXT,
        resident_type TEXT DEFAULT 'Owner' CHECK(resident_type IN ('Owner', 'Tenant')),
        family_members INTEGER DEFAULT 1,
        vehicle_number TEXT,
        status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        flat_id INTEGER NOT NULL,
        vehicle_number TEXT NOT NULL UNIQUE,
        vehicle_type TEXT DEFAULT 'Car' CHECK(vehicle_type IN ('Car', 'Bike', 'Scooter', 'Other')),
        owner_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
        FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flat_id INTEGER NOT NULL,
        month_year TEXT NOT NULL,
        maintenance_amount REAL NOT NULL DEFAULT 3000.00,
        parking_amount REAL NOT NULL DEFAULT 500.00,
        other_amount REAL NOT NULL DEFAULT 200.00,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'PARTIAL', 'PAID')),
        due_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        maintenance_id INTEGER NOT NULL,
        flat_id INTEGER NOT NULL,
        amount_paid REAL NOT NULL,
        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        payment_mode TEXT DEFAULT 'UPI',
        reference_no TEXT,
        receipt_no TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (maintenance_id) REFERENCES maintenance(id) ON DELETE CASCADE,
        FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resident_id INTEGER,
        flat_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL CHECK(category IN ('Plumbing', 'Electrical', 'Lift', 'Cleaning', 'Security', 'Parking', 'Other')),
        description TEXT NOT NULL,
        photo_path TEXT,
        status TEXT DEFAULT 'OPEN' CHECK(status IN ('OPEN', 'IN PROGRESS', 'RESOLVED', 'CLOSED')),
        admin_response TEXT,
        assigned_to TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
        FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        visitor_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        flat_id INTEGER NOT NULL,
        purpose TEXT NOT NULL,
        vehicle_number TEXT,
        entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        exit_time TIMESTAMP,
        status TEXT DEFAULT 'Inside' CHECK(status IN ('Inside', 'Exited')),
        recorded_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE,
        FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        description TEXT NOT NULL,
        published_date DATE NOT NULL,
        created_by INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    );
    ''')

    # Seed data if users table is empty
    cur.execute("SELECT COUNT(*) as cnt FROM users")
    if cur.fetchone()['cnt'] == 0:
        # Default accounts (passwords: admin123, resident123, security123)
        pw_admin = generate_password_hash('admin123')
        pw_resident = generate_password_hash('resident123')
        pw_security = generate_password_hash('security123')

        cur.execute("INSERT INTO users (username, password, role, full_name, phone) VALUES (?, ?, ?, ?, ?)",
                    ('admin', pw_admin, 'admin', 'Society Secretary (Admin)', '9820011223'))
        cur.execute("INSERT INTO users (username, password, role, full_name, phone) VALUES (?, ?, ?, ?, ?)",
                    ('resident', pw_resident, 'resident', 'Rahul Sharma', '9876543210'))
        cur.execute("INSERT INTO users (username, password, role, full_name, phone) VALUES (?, ?, ?, ?, ?)",
                    ('security', pw_security, 'security', 'Main Gate Guard (Security)', '9811122233'))

        # Flats
        flats_data = [
            ('A-101', 'A', 1, '2BHK', 'Rahul Sharma', '9876543210', 'Rahul Sharma', '9876543210', 'Occupied'),
            ('A-102', 'A', 1, '2BHK', 'Amit Verma', '9876543211', 'Vikas Patel', '9876543212', 'Occupied'),
            ('A-201', 'A', 2, '3BHK', 'Sunita Rao', '9876543213', None, None, 'Vacant'),
            ('A-202', 'A', 2, '3BHK', 'Rohan Mehta', '9876543214', 'Rohan Mehta', '9876543214', 'Occupied'),
            ('B-101', 'B', 1, '2BHK', 'Deepak Kumar', '9876543215', 'Deepak Kumar', '9876543215', 'Occupied'),
            ('B-102', 'B', 1, '2BHK', 'Priya Nair', '9876543216', 'Priya Nair', '9876543216', 'Occupied'),
            ('B-201', 'B', 2, '3BHK', 'Kavita Joshi', '9876543217', None, None, 'Vacant'),
            ('B-202', 'B', 2, '3BHK', 'Suresh Gupta', '9876543218', 'Suresh Gupta', '9876543218', 'Occupied')
        ]
        cur.executemany('''
            INSERT INTO flats (flat_number, wing, floor, flat_type, owner_name, owner_phone, resident_name, resident_phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', flats_data)

        # Residents
        residents_data = [
            (2, 1, 'Rahul Sharma', '9876543210', 'rahul@society.com', 'Owner', 3, 'MH-02-AB-1234', 'Active'),
            (None, 2, 'Vikas Patel', '9876543212', 'vikas.patel@gmail.com', 'Tenant', 2, 'MH-04-CD-5678', 'Active'),
            (None, 4, 'Rohan Mehta', '9876543214', 'rohan.mehta@yahoo.com', 'Owner', 4, 'MH-02-XY-9999', 'Active'),
            (None, 5, 'Deepak Kumar', '9876543215', 'deepak.k@gmail.com', 'Owner', 2, 'MH-03-JK-3421', 'Active'),
            (None, 6, 'Priya Nair', '9876543216', 'priya.nair@outlook.com', 'Owner', 3, 'MH-02-MN-4321', 'Active'),
            (None, 8, 'Suresh Gupta', '9876543218', 'suresh.gupta@gmail.com', 'Owner', 5, 'MH-01-PQ-7788', 'Active')
        ]
        cur.executemany('''
            INSERT INTO residents (user_id, flat_id, name, mobile, email, resident_type, family_members, vehicle_number, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', residents_data)

        # Vehicles
        vehicles_data = [
            (1, 1, 'MH-02-AB-1234', 'Car', 'Rahul Sharma'),
            (1, 1, 'MH-02-CZ-4321', 'Bike', 'Rahul Sharma'),
            (2, 2, 'MH-04-CD-5678', 'Car', 'Vikas Patel'),
            (3, 4, 'MH-02-XY-9999', 'Car', 'Rohan Mehta'),
            (4, 5, 'MH-03-JK-3421', 'Bike', 'Deepak Kumar'),
            (5, 6, 'MH-02-MN-4321', 'Car', 'Priya Nair')
        ]
        cur.executemany('''
            INSERT INTO vehicles (resident_id, flat_id, vehicle_number, vehicle_type, owner_name)
            VALUES (?, ?, ?, ?, ?)
        ''', vehicles_data)

        # Maintenance Records
        maint_data = [
            (1, 'October 2026', 3000.0, 500.0, 200.0, 3700.0, 'PAID', '2026-10-15'),
            (2, 'October 2026', 3000.0, 500.0, 200.0, 3700.0, 'PENDING', '2026-10-15'),
            (4, 'October 2026', 3500.0, 500.0, 200.0, 4200.0, 'PAID', '2026-10-15'),
            (5, 'October 2026', 3000.0, 250.0, 200.0, 3450.0, 'PENDING', '2026-10-15'),
            (6, 'October 2026', 3000.0, 500.0, 200.0, 3700.0, 'PAID', '2026-10-15'),
            (8, 'October 2026', 3500.0, 500.0, 200.0, 4200.0, 'PENDING', '2026-10-15'),
            (1, 'September 2026', 3000.0, 500.0, 200.0, 3700.0, 'PAID', '2026-09-15'),
            (2, 'September 2026', 3000.0, 500.0, 200.0, 3700.0, 'PAID', '2026-09-15')
        ]
        cur.executemany('''
            INSERT INTO maintenance (flat_id, month_year, maintenance_amount, parking_amount, other_amount, total_amount, status, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', maint_data)

        # Payments for Paid Maintenance
        payments_data = [
            (1, 1, 3700.0, '2026-10-02 11:20:00', 'UPI', 'UPI/261002/1001', 'REC-2026-1001'),
            (3, 4, 4200.0, '2026-10-03 14:15:00', 'NetBanking', 'HDFC-TXN-88219', 'REC-2026-1002'),
            (5, 6, 3700.0, '2026-10-04 09:45:00', 'UPI', 'GPAY-83921932', 'REC-2026-1003'),
            (7, 1, 3700.0, '2026-09-05 10:10:00', 'Cheque', 'CHQ-445521', 'REC-2026-0901'),
            (8, 2, 3700.0, '2026-09-08 16:30:00', 'UPI', 'UPI/260908/3920', 'REC-2026-0902')
        ]
        cur.executemany('''
            INSERT INTO payments (maintenance_id, flat_id, amount_paid, payment_date, payment_mode, reference_no, receipt_no)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', payments_data)

        # Complaints
        complaints_data = [
            (1, 1, 'Water leakage in master bathroom ceiling', 'Plumbing', 'Water is dripping slowly from the ceiling of the master bathroom since yesterday evening.', 'IN PROGRESS', 'Plumber assigned. Inspection scheduled for today at 3:00 PM.', 'Ramesh (Society Plumber)'),
            (2, 2, 'Main staircase tube light flickering', 'Electrical', 'The corridor lighting on 1st floor Wing A is flickering continuously.', 'RESOLVED', 'Replaced with a new 20W LED batten on Oct 4.', 'Mahesh Electrician'),
            (3, 4, 'Wing B Lift Jerking between 1st & 2nd Floor', 'Lift', 'The lift makes an unusual vibration and slight jerk while descending between 2nd and 1st floor.', 'OPEN', None, None),
            (5, 6, 'Unauthorised car parked in slot B-6', 'Parking', 'A white Swift is parked in my assigned parking bay B-6 without permission.', 'RESOLVED', 'Security notified car owner to relocate vehicle.', 'Security Desk')
        ]
        cur.executemany('''
            INSERT INTO complaints (resident_id, flat_id, title, category, description, status, admin_response, assigned_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', complaints_data)

        # Visitors
        visitors_data = [
            ('Sunil Gavaskar', '9820123456', 1, 'Personal Guest', 'MH-01-BB-4422', '2026-10-05 09:30:00', None, 'Inside', 3),
            ('Amazon Delivery Agent', '9988776655', 2, 'Parcel Delivery', 'MH-03-ZZ-1100', '2026-10-05 10:15:00', '2026-10-05 10:35:00', 'Exited', 3),
            ('Urban Company Technician', '9812345678', 6, 'AC Servicing', 'MH-02-TR-9090', '2026-10-05 10:45:00', None, 'Inside', 3),
            ('Swiggy Delivery Boy', '9700112233', 4, 'Food Delivery', None, '2026-10-04 19:20:00', '2026-10-04 19:40:00', 'Exited', 3),
            ('Aakash Singhania', '9833445566', 1, 'Family Visit', 'MH-04-EE-3214', '2026-10-04 15:00:00', '2026-10-04 18:30:00', 'Exited', 3)
        ]
        cur.executemany('''
            INSERT INTO visitors (visitor_name, phone, flat_id, purpose, vehicle_number, entry_time, exit_time, status, recorded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', visitors_data)

        # Notices
        notices_data = [
            ('Annual General Meeting (AGM) Notice', 'Meeting', 'The 12th Annual General Body Meeting will be held on Sunday, October 18, 2026 at 10:30 AM in the Society Clubhouse. All members are requested to attend.', '2026-10-01', 1, 1),
            ('Water Supply Maintenance & Tank Cleaning', 'Maintenance', 'Overhead water tank cleaning is scheduled for Thursday, October 8, from 9:00 AM to 2:00 PM. Water supply will be restricted during these hours.', '2026-10-03', 1, 1),
            ('Diwali Festival Celebration & Cultural Evening', 'Event', 'Join us for Diwali sweets distribution and children cultural performances on Oct 25, 6:00 PM onwards in the central garden area.', '2026-10-04', 1, 1),
            ('Updated Visitor Vehicle Parking Rules', 'Security', 'All visiting vehicles must park strictly in designated guest bays G1–G10. No parking is permitted in fire lanes.', '2026-09-28', 1, 1)
        ]
        cur.executemany('''
            INSERT INTO notices (title, category, description, published_date, created_by, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', notices_data)

    conn.commit()
    conn.close()
    return True

# Initialize database automatically when imported
init_database()
