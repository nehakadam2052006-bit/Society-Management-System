-- ==============================================================
-- Simple Housing Society Management System - Database Schema
-- Database: society_db
-- ==============================================================

CREATE DATABASE IF NOT EXISTS society_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE society_db;

-- 1. USERS TABLE
-- Roles: 'admin', 'resident', 'security'
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'resident', 'security') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. FLATS TABLE
-- Stores society flats and occupancy details
CREATE TABLE IF NOT EXISTS flats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flat_number VARCHAR(20) NOT NULL UNIQUE,
    wing VARCHAR(10) NOT NULL,
    floor INT NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    owner_phone VARCHAR(20) NOT NULL,
    resident_name VARCHAR(100) NULL,
    resident_phone VARCHAR(20) NULL,
    status ENUM('Occupied', 'Vacant') DEFAULT 'Vacant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. RESIDENTS TABLE
-- Detailed resident profile linked to flat and optional user login
CREATE TABLE IF NOT EXISTS residents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    flat_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    mobile VARCHAR(20) NOT NULL,
    email VARCHAR(100) NULL,
    resident_type ENUM('Owner', 'Tenant') NOT NULL DEFAULT 'Owner',
    family_members INT DEFAULT 1,
    vehicle_number VARCHAR(50) NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. VEHICLES TABLE
-- Vehicle records linked to resident and flat
CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT NULL,
    flat_id INT NOT NULL,
    vehicle_number VARCHAR(50) NOT NULL UNIQUE,
    vehicle_type ENUM('Car', 'Bike', 'Scooter', 'Other') NOT NULL DEFAULT 'Car',
    owner_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. MAINTENANCE TABLE
-- Monthly maintenance bills for flats
CREATE TABLE IF NOT EXISTS maintenance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flat_id INT NOT NULL,
    month_year VARCHAR(20) NOT NULL,
    maintenance_amount DECIMAL(10,2) NOT NULL DEFAULT 3000.00,
    parking_amount DECIMAL(10,2) NOT NULL DEFAULT 500.00,
    other_amount DECIMAL(10,2) NOT NULL DEFAULT 200.00,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('PENDING', 'PARTIAL', 'PAID') DEFAULT 'PENDING',
    due_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. PAYMENTS TABLE
-- Payment records for maintenance bills
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    maintenance_id INT NOT NULL,
    flat_id INT NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_mode VARCHAR(50) DEFAULT 'Online',
    reference_no VARCHAR(100) NULL,
    receipt_no VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (maintenance_id) REFERENCES maintenance(id) ON DELETE CASCADE,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. COMPLAINTS TABLE
-- Complaints raised by residents
CREATE TABLE IF NOT EXISTS complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resident_id INT NULL,
    flat_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    category ENUM('Plumbing', 'Electrical', 'Lift', 'Cleaning', 'Security', 'Parking', 'Other') NOT NULL,
    description TEXT NOT NULL,
    photo_path VARCHAR(255) NULL,
    status ENUM('OPEN', 'IN PROGRESS', 'RESOLVED', 'CLOSED') DEFAULT 'OPEN',
    admin_response TEXT NULL,
    assigned_to VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (resident_id) REFERENCES residents(id) ON DELETE SET NULL,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. VISITORS TABLE
-- Visitor entry and exit logs managed by security
CREATE TABLE IF NOT EXISTS visitors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    visitor_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    flat_id INT NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    vehicle_number VARCHAR(50) NULL,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP NULL,
    status ENUM('Inside', 'Exited') DEFAULT 'Inside',
    recorded_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flat_id) REFERENCES flats(id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. NOTICES TABLE
-- Notices published by admin
CREATE TABLE IF NOT EXISTS notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    published_date DATE NOT NULL,
    created_by INT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==============================================================
-- INITIAL SEED DATA
-- Default accounts (Password for all 3 demo accounts: username + "123")
-- admin / admin123
-- resident / resident123
-- security / security123
-- ==============================================================

INSERT IGNORE INTO users (id, username, password, role) VALUES
(1, 'admin', 'scrypt:32768:8:1$MWvcCyFW0pndkk29$b14525ff6acca6da9d25341e2a4f768c61cf13af7be8f7864c42c0c3d5ba18348b4d6626d0834ad0cf94d63f5ccee29b945f61b0f279cb2c592f4f8b4196f237', 'admin'),
(2, 'resident', 'scrypt:32768:8:1$Otz6OBnixvhJI11F$dd734bbfe362da5a73fc3e9758b8767cb2eaa9f476a73b5a029498b1b84e5c732c62253dfa75e1b8c1dcc6ec50110e60330dd86081af7b4f0fe25dc9eff77e1f', 'resident'),
(3, 'security', 'scrypt:32768:8:1$q4wXA7At6xr2tO6a$8f48a0f0143e8c522e8833f4d3a7a05b057094d319bc0c79aa4d8415b99361f2279b6d10ecc506ad17151e4d89f4e71d3f9334fb120cf22f42598fbfcdba2d6f', 'security');

-- Sample Flats
INSERT IGNORE INTO flats (id, flat_number, wing, floor, owner_name, owner_phone, resident_name, resident_phone, status) VALUES
(1, 'A-101', 'A', 1, 'Rahul Sharma', '9876543210', 'Rahul Sharma', '9876543210', 'Occupied'),
(2, 'A-102', 'A', 1, 'Amit Verma', '9876543211', 'Vikas Patel', '9876543212', 'Occupied'),
(3, 'A-103', 'A', 1, 'Sunita Rao', '9876543213', NULL, NULL, 'Vacant'),
(4, 'B-101', 'B', 1, 'Deepak Kumar', '9876543214', 'Deepak Kumar', '9876543214', 'Occupied'),
(5, 'B-102', 'B', 1, 'Priya Nair', '9876543215', NULL, NULL, 'Vacant');

-- Sample Resident (linked to user 2 - resident)
INSERT IGNORE INTO residents (id, user_id, flat_id, name, mobile, email, resident_type, family_members, vehicle_number, status) VALUES
(1, 2, 1, 'Rahul Sharma', '9876543210', 'rahul@example.com', 'Owner', 3, 'MH-02-AB-1234', 'Active');

-- Sample Notice
INSERT IGNORE INTO notices (id, title, description, published_date, created_by, is_active) VALUES
(1, 'Welcome to Society Portal', 'Welcome to our residential society management portal. Please check your dues and raise complaints online.', CURDATE(), 1, TRUE);
