# University Navigation System — Backend (FastAPI)

Bu servis bino ichida navigatsiya (qavat → waypoint → connection → pathfinding) uchun API beradi.

## Talablar

- Docker Desktop + Docker Compose v2
- `make` (ixtiyoriy, lekin qulay)

Agar Docker ishlatmasangiz:
- Python 3.11+
- PostgreSQL 15+

## Tezkor Boshlash

### 1) `.env` tayyorlang

```bash
cd bino_xarita_admin
cp .env.example .env
```

**Production'da albatta o'zgartiring:**
- `SECRET_KEY` (kamida 32 belgi)
- `JWT_SECRET_KEY` (kamida 32 belgi, `SECRET_KEY` dan farqli)
- `ADMIN_TOKEN` (kamida 32 belgi)
- `ALLOWED_ORIGINS` (prod'da `*` bo'lmasin)
- `ENV=production`

### 2) Frontend nomi

Agar frontend Git'dan boshqa nom bilan tushgan bo'lsa, `.env` da o'zgartiring:

```bash
# GitHub: https://github.com/uni-nav/campus-navigator-1
FRONTEND_DIR=campus-navigator-1
```

### 3) Portlarni sozlash

```bash
# .env da:
API_PORT=8000
FRONTEND_PORT=8080
```

### 4) Ishga tushirish

```bash
# Development
make dev-d
make migrate
make test

# Production
make prod
make migrate
```

## Kirish manzillari

| Servis | URL |
|--------|-----|
| API | `http://localhost:${API_PORT}` |
| Swagger | `http://localhost:${API_PORT}/docs` |
| Frontend | `http://localhost:${FRONTEND_PORT}` |

## Admin autentifikatsiya

Admin endpointlar uchun header:
```
Authorization: Bearer <ADMIN_TOKEN>
```

JWT login: `/api/auth/login`

## Asosiy komandalar (Docker Compose)

### Ishga tushirish

```bash
# Development (loglarni ko'rish uchun)
docker compose up --build

# Development (orqa fonda / detached)
docker compose up --build -d

# To'xtatish
docker compose down
```

### Loglarni ko'rish

```bash
# Hamma loglar
docker compose logs -f

# Faqat API loglari
docker compose logs -f api

# Faqat DB loglari
docker compose logs -f db
```

### Database Migrations (Alembic)

```bash
docker compose exec -T api alembic upgrade head
```

### Database Backup & Restore

```bash
# Backup olish (backups papkasiga)
mkdir -p backups
docker compose exec -T db sh -lc 'pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' > backups/db_backup.sql

# Restore qilish (backups/db_backup.sql faylidan)
cat backups/db_backup.sql | docker compose exec -T db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'
```

### Testlarni ishlatish

```bash
docker compose exec -T api python -m pytest
```

### API Health Check (Internal)

API faqat ichki tarmoqda bo'lgani uchun, tekshirish quyidagicha:

```bash
docker compose exec -T api curl -s http://localhost:8000/api/health
```

### Ma'lumotlarni tozalash (Reset DB)

```bash
docker compose down -v
```

