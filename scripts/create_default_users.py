"""Create the 4 default demo users."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.user_manager import create_user, get_user

USERS = [
    ('admin',       'admin123',      'System Administrator',  'admin@hmrl.com',       'Admin'),
    ('scheduler',   'scheduler123',  'Schedule Manager',      'scheduler@hmrl.com',   'Scheduler'),
    ('maintenance', 'maint123',      'Maintenance Team Lead', 'maint@hmrl.com',        'Maintenance_Team'),
    ('viewer',      'viewer123',     'Operations Viewer',     'viewer@hmrl.com',       'Viewer'),
]

for username, password, full_name, email, role in USERS:
    if get_user(username):
        print(f"  [SKIP] {username} already exists")
    else:
        ok = create_user(username, password, full_name, email, role)
        print(f"  {'[OK]  ' if ok else '[FAIL]'} {username} ({role})")

print("\nDefault users ready. Login with admin / admin123")
