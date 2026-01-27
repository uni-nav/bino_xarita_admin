# 🔐 Authentication Usage Guide

## Backend - Protected Endpoints

### Example: Protected DELETE endpoint

```python
# app/api/floors.py
from app.core.auth import verify_admin_token

@router.delete("/{floor_id}")
def delete_floor(
    floor_id: int,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_admin_token)  # ✅ Requires admin token
):
    # Only accessible with valid admin token
    ...
```

### Testing with curl:

```bash
# Without token - 401 Unauthorized
curl -X DELETE http://localhost:8000/api/floors/1

# With token - Success
curl -X DELETE http://localhost:8000/api/floors/1 \
  -H "Authorization: Bearer my_secure_admin_token_2026"
```

## Frontend - Adding Authorization Header

### Update axios client:

```typescript
// frontend/src/lib/api/client.ts

const ADMIN_TOKEN_KEY = 'admin_token';

export const getAdminToken = (): string | null => {
  return localStorage.getItem(ADMIN_TOKEN_KEY);
};

export const setAdminToken = (token: string): void => {
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
};

const createClient = (): AxiosInstance => {
  const token = getAdminToken();
  const headers: any = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return axios.create({
    baseURL: getApiUrl(),
    headers,
  });
};
```

### Login component (simple):

```typescript
// frontend/src/pages/LoginPage.tsx
import { setAdminToken } from '@/lib/api/client';

function LoginPage() {
  const [token, setToken] = useState('');
  
  const handleLogin = () => {
    setAdminToken(token);
    navigate('/floors');
  };
  
  return (
    <div>
      <Input 
        type="password"
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="Admin Token"
      />
      <Button onClick={handleLogin}>Login</Button>
    </div>
  );
}
```

## Configuration

### .env file:
```
ADMIN_TOKEN=my_secure_admin_token_2026
```

### Which endpoints to protect?

✅ **Protect these (destructive operations):**
- DELETE endpoints (delete_floor, delete_waypoint, etc.)
- POST /floors (create)
- PUT /floors/{id} (update)
- POST /floors/{id}/upload-image

🔓 **Keep public:**
- GET /api/navigation/find-path (kiosk needs this)
- GET /api/rooms/search
- GET /health

## Next Steps for Production:

1. **JWT Tokens** instead of static token
2. **User roles** (admin, editor, viewer)
3. **Token expiration**
4. **Refresh tokens**

Use `fastapi-users` or `python-jose` for full JWT implementation.
