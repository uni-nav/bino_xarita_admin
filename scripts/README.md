# Admin Management Scripts

## Create Admin User

### Interactive Mode
```bash
python3 scripts/create_admin.py
```

The script will prompt you for:
- Username (default: admin)
- Password (must be 8+ chars with uppercase, lowercase, and digits)
- Password confirmation

### Password Requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### Output
The script will generate:
```
ADMIN_USERNAME=your_username
ADMIN_PASSWORD_HASH="$2b$12$..."
```

These will be automatically appended to your `.env` file if you confirm.

### Manual Setup
If you prefer to add credentials manually:

1. Generate password hash:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash = pwd_context.hash("YOUR_SECURE_PASSWORD")
print(hash)
```

2. Add to `.env`:
```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH="$2b$12$..."
```

## Security Notes

⚠️ **Important**:
- Never commit `.env` file to Git (already in `.gitignore`)
- Use strong, unique passwords for production
- Password cannot be recovered, only reset
- Change default admin credentials immediately in production

## Fallback Behavior

If `ADMIN_PASSWORD_HASH` is not set in `.env`:
- Development: Falls back to insecure default password "admin123456"
- Warning is logged on startup
- **This is insecure and only for local development**

## Production Deployment

1. Run the script before deployment:
   ```bash
   python3 scripts/create_admin.py
   ```

2. Verify `.env` has both:
   ```bash
   ADMIN_USERNAME=<your_username>
   ADMIN_PASSWORD_HASH="<bcrypt_hash>"
   ```

3. Deploy application

4. Test login:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "your_username", "password": "your_password"}'
   ```

## Future: Database-Backed Users

This in-memory user system is temporary. Future versions will include:
- User database table with proper schema
- User registration API
- Password reset functionality
- Role-based access control (RBAC)
- Multi-admin support
