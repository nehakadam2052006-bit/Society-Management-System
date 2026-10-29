import os
import subprocess
import time

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = "report_assets/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

PAGES = [
    ("fig07_login.png", "http://127.0.0.1:5001/login", 1280, 800),
    ("fig08_admin_dashboard.png", "http://127.0.0.1:5001/dev-preview/admin/admin_dashboard", 1280, 900),
    ("fig09_flats_management.png", "http://127.0.0.1:5001/dev-preview/admin/flats", 1280, 850),
    ("fig10_resident_directory.png", "http://127.0.0.1:5001/dev-preview/admin/residents", 1280, 850),
    ("fig11_maintenance_billing.png", "http://127.0.0.1:5001/dev-preview/admin/maintenance", 1280, 900),
    ("fig12_payment_receipt.png", "http://127.0.0.1:5001/receipt/1", 1280, 950),
    ("fig13_complaints_admin.png", "http://127.0.0.1:5001/dev-preview/admin/complaints", 1280, 850),
    ("fig14_visitor_management.png", "http://127.0.0.1:5001/dev-preview/admin/visitors", 1280, 900),
    ("fig15_society_notices.png", "http://127.0.0.1:5001/dev-preview/admin/notices", 1280, 850),
    ("fig16_vehicle_directory.png", "http://127.0.0.1:5001/dev-preview/admin/vehicles", 1280, 800),
    ("fig17_reports_analytics.png", "http://127.0.0.1:5001/dev-preview/admin/reports", 1280, 800),
    ("fig18_resident_dashboard.png", "http://127.0.0.1:5001/dev-preview/resident/resident_dashboard", 1280, 850),
    ("fig19_resident_bills.png", "http://127.0.0.1:5001/dev-preview/resident/resident_bills", 1280, 800),
    ("fig20_resident_complaints.png", "http://127.0.0.1:5001/dev-preview/resident/resident_complaints", 1280, 850),
    ("fig21_security_dashboard.png", "http://127.0.0.1:5001/dev-preview/security/security_dashboard", 1280, 850),
]

def main():
    print(f"Capturing {len(PAGES)} screenshots using Chrome headless...")
    for filename, url, width, height in PAGES:
        out_path = os.path.join(OUT_DIR, filename)
        cmd = [
            CHROME_BIN,
            "--headless",
            "--disable-gpu",
            f"--screenshot={out_path}",
            f"--window-size={width},{height}",
            url
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            if os.path.exists(out_path):
                print(f"✓ Saved {filename} ({os.path.getsize(out_path)} bytes)")
            else:
                print(f"✗ Failed to capture {filename}")
        except Exception as e:
            print(f"Error on {filename}: {e}")
        time.sleep(0.5)

if __name__ == '__main__':
    main()
