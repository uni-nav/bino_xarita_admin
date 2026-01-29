# Security Configuration Guide

## Generate Strong Secret Keys

To generate secure secret keys for production:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this command **twice** to generate two different keys:
1. One for `SECRET_KEY`
2. One for `JWT_SECRET_KEY`

## Required Environment Variables for Production

### 1. Database
```bash
DB_USER=your_db_username
DB_PASSWORD=strong_database_password
DB_NAME=university_nav
DB_HOST=your_db_host  # e.g., localhost or db service name
DB_PORT=5432
```

### 2. Security Keys
```bash
SECRET_KEY=<generated-key-32-chars-minimum>
JWT_SECRET_KEY=<different-generated-key-32-chars>
ADMIN_TOKEN=<your-admin-token-32-chars>
```

### 3. JWT Settings
```bash
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30  # Adjust as needed
```

### 4. Environment
```bash
ENV=production  # Options: development, staging, production
DEBUG=false
```

## Default Admin Credentials (TEMPORARY)

**⚠️ WARNING: These are temporary credentials for initial setup**

- **Username:** `admin`
- **Password:** `admin123456`

### How to login and get JWT token:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123456"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the JWT token:

```bash
# Use the token in Authorization header
curl http://localhost:8000/api/floors/ \
  -H "Authorization: Bearer <your-token-here>"
```

## Migration from Legacy Token to JWT

The system currently supports **both** authentication methods:

1. **Legacy Token** (will be deprecated):
   ```bash
   curl http://localhost:8000/api/floors/ \
     -H "Authorization: Bearer your-admin-token"
   ```

2. **JWT Token** (recommended):
   ```bash
   # Step 1: Login to get JWT
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123456"}'
   
   # Step 2: Use JWT token
   curl http://localhost:8000/api/floors/ \
     -H "Authorization: Bearer <jwt-token>"
   ```

## Production TODO

- [ ] Implement database-backed user management
- [ ] Add user registration endpoint
- [ ] Add password reset functionality
- [ ] Implement token refresh mechanism
- [ ] Add rate limiting for login attempts
- [ ] Add 2FA support
- [ ] Change default admin password
- [ ] Set up proper RBAC (Role-Based Access Control)

## Docker Secret Management

For production deployment with Docker Swarm:

```bash
# Create secrets
echo "your-secret-key" | docker secret create db_password -
echo "your-jwt-key" | docker secret create jwt_secret -

# Update docker-compose.prod.yml to use secrets
```
