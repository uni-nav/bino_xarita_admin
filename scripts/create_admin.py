#!/usr/bin/env python3
"""
Admin User Creation Script
Usage: python scripts/create_admin.py
"""
import os
import sys
import getpass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.security import get_password_hash
from passlib.context import CryptContext

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and digits"
    
    return True, "Password is strong"


def create_admin_user():
    """Interactive admin user creation"""
    print("=" * 60)
    print("        ADMIN USER CREATION SCRIPT")
    print("=" * 60)
    print()
    
    # Get username
    username = input("Enter admin username [default: admin]: ").strip()
    if not username:
        username = "admin"
    
    if len(username) < 3:
        print("❌ Username must be at least 3 characters")
        sys.exit(1)
    
    # Get password
    while True:
        password = getpass.getpass("Enter admin password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match. Try again.\n")
            continue
        
        is_valid, message = validate_password(password)
        if not is_valid:
            print(f"❌ {message}\n")
            continue
        
        break
    
    # Hash password
    print("\n⏳ Hashing password...")
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash(password)
    
    # Generate environment variables
    print("\n✅ Admin user created successfully!")
    print("\n" + "=" * 60)
    print("Add these to your .env file:")
    print("=" * 60)
    print(f"ADMIN_USERNAME={username}")
    print(f'ADMIN_PASSWORD_HASH="{hashed_password}"')
    print("=" * 60)
    
    # Offer to append to .env
    env_path = project_root / ".env"
    if env_path.exists():
        append = input("\nAppend to .env file automatically? [y/N]: ").strip().lower()
        if append == 'y':
            with open(env_path, 'a') as f:
                f.write(f"\n# Admin User Credentials (Generated {os.popen('date').read().strip()})\n")
                f.write(f"ADMIN_USERNAME={username}\n")
                f.write(f'ADMIN_PASSWORD_HASH="{hashed_password}"\n')
            print("✅ Credentials appended to .env file")
        else:
            print("\n⚠️  Please manually add the credentials to your .env file")
    
    print("\n🔐 Security Notes:")
    print("   - Keep your .env file secure and never commit it to Git")
    print("   - The password cannot be recovered, only reset")
    print("   - Use strong, unique passwords for production")
    print()


if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
