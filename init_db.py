"""
Database Initialization Script
Run this script to initialize the database:
    python init_db.py
"""
import os
import sys
from db import init_database, check_db_status

def main():
    print("=" * 60)
    print("Housing Society Management System - Database Initializer")
    print("=" * 60)
    print("Initializing database tables and seed data...")
    try:
        init_database(force=True)
        status = check_db_status()
        if status['connected']:
            print("✓ Database initialized successfully!")
            print(f"Engine: {status['engine']}")
            print(f"Database location: {status['db_file']}")
            print(f"Total Tables ({len(status['tables'])}):")
            for table in status['tables']:
                cnt = status['counts'].get(table, 0)
                print(f"   • {table} ({cnt} records)")
            print("=" * 60)
            print("Default Demo Accounts:")
            print("  • Admin:    username='admin'    password='admin123'")
            print("  • Resident: username='resident' password='resident123'")
            print("  • Security: username='security' password='security123'")
            print("=" * 60)
            return True
        else:
            print(f"✗ Database check failed: {status['error']}")
            return False
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)
