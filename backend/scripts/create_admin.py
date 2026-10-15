import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.security.hashing import hash_password

def create_admin(email: str, password: str, full_name: str, role: str = UserRole.SUPER_ADMIN):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email.lower().strip()).first()
        if existing:
            print(f"[!] User with email '{email}' already exists. Updating password and role...")
            existing.hashed_password = hash_password(password)
            existing.role = role
            existing.is_active = True
            db.commit()
            print(f"[+] Updated user '{email}' to role '{role}'.")
            return
        
        user = User(
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        print(f"[+] Created user '{email}' successfully with role '{role}'.")
    except Exception as e:
        print(f"[-] Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap administrator account for LogSentinel")
    parser.add_argument("--email", default="admin@logsentinel.local", help="Admin email")
    parser.add_argument("--password", default="AdminSecurePass123!", help="Admin password")
    parser.add_argument("--name", default="Super Administrator", help="Admin full name")
    parser.add_argument("--role", default="super_admin", choices=["super_admin", "engineer", "viewer"], help="User role")

    args = parser.parse_args()
    create_admin(args.email, args.password, args.name, args.role)
