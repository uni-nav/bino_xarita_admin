
# README.md ishga tushirish bo'yicha qo'llanma

# University Navigation System - Backend API

## O'rnatish va Ishga Tushirish

### 1. Talablar
- Python 3.11+
- PostgreSQL 15+ yoki Docker
- pip

### 2. Lokal o'rnatish (Mac uchun)

```bash
# 1. Repository ni clone qiling
git clone <your-repo>
cd university-navigation-backend

# 2. Virtual environment yarating
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies o'rnating
pip install -r requirements.txt

# 4. PostgreSQL o'rnating (agar yo'q bo'lsa)
brew install postgresql@15
brew services start postgresql@15

# 5. Database yarating
createdb university_nav

# 6. .env faylni yarating va sozlang
cp .env.example .env
# .env faylini tahrirlang

# 7. Database migration
alembic upgrade head

# 8. Serverni ishga tushiring
uvicorn app.main:app --reload
```

### 3. Docker bilan ishga tushirish (Tavsiya etiladi)

```bash
# 1. Docker Desktop o'rnating (Mac uchun)

# 2. Serverni ishga tushiring
docker-compose up -d

# 3. Loglarni ko'ring
docker-compose logs -f api

# 4. Database migration
docker-compose exec api alembic upgrade head

# 5. To'xtatish
docker-compose down
```

### 4. API Documentation

Server ishga tushgandan keyin:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 5. API Endpoints

#### Floors
- GET    /api/floors         - Barcha qavatlar
- GET    /api/floors/{id}    - Bitta qavat
- POST   /api/floors         - Yangi qavat
- PUT    /api/floors/{id}    - Qavatni yangilash
- DELETE /api/floors/{id}    - Qavatni o'chirish
- POST   /api/floors/{id}/upload-image - Rasm yuklash

#### Waypoints
- GET    /api/waypoints/floor/{floor_id} - Qavat bo'yicha nuqtalar
- GET    /api/waypoints/{id}             - Bitta nuqta
- POST   /api/waypoints                  - Yangi nuqta
- POST   /api/waypoints/batch            - Ko'p nuqtalar
- PUT    /api/waypoints/{id}             - Nuqtani yangilash
- DELETE /api/waypoints/{id}             - Nuqtani o'chirish

#### Connections
- POST   /api/waypoints/connections       - Bog'lanish yaratish
- POST   /api/waypoints/connections/batch - Ko'p bog'lanishlar
- GET    /api/waypoints/connections/floor/{floor_id} - Qavat bo'yicha

#### Navigation
- POST   /api/navigation/find-path        - Yo'l topish
- GET    /api/navigation/nearby-rooms/{waypoint_id} - Yaqin xonalar

#### Rooms
- GET    /api/rooms                  - Barcha xonalar
- GET    /api/rooms/floor/{floor_id} - Qavat bo'yicha xonalar
- GET    /api/rooms/search?query=101 - Xonalarni qidirish
- POST   /api/rooms                  - Yangi xona
- POST   /api/rooms/batch            - Ko'p xonalar

### 6. Test qilish

```bash
# Curl bilan test
curl http://localhost:8000/health

# Floor yaratish
curl -X POST http://localhost:8000/api/floors \
  -H "Content-Type: application/json" \
  -d '{"name": "1-qavat", "floor_number": 1}'

# Waypoint yaratish
curl -X POST http://localhost:8000/api/waypoints \
  -H "Content-Type: application/json" \
  -d '{
    "id": "wp-001",
    "floor_id": 1,
    "x": 100,
    "y": 200,
    "type": "hallway"
  }'

# Yo'l topish
curl -X POST http://localhost:8000/api/navigation/find-path \
  -H "Content-Type: application/json" \
  -d '{
    "start_waypoint_id": "wp-001",
    "end_waypoint_id": "wp-050"
  }'
```

### 7. Production uchun

```bash
# 1. SECRET_KEY ni o'zgartiring
# 2. PostgreSQL passwordini o'zgartiring
# 3. CORS settingsni cheklang
# 4. HTTPS o'rnating
# 5. Rate limiting qo'shing
# 6. Monitoring o'rnating

# Production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 8. Troubleshooting

```bash
# Database connection muammosi
# .env faylda DATABASE_URL to'g'riligini tekshiring

# Port band bo'lsa
lsof -ti:8000 | xargs kill -9

# Docker muammolari
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```