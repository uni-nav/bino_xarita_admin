
# Makefile (yordamchi komandalar)
.PHONY: help install dev migrate upgrade test

help:
	@echo "University Navigation API - Commands"
	@echo "  make install    - O'rnatish"
	@echo "  make dev        - Development server"
	@echo "  make migrate    - Database migration yaratish"
	@echo "  make upgrade    - Database upgrade"
	@echo "  make test       - Testlarni ishga tushirish"
	@echo "  make docker-up  - Docker bilan ishga tushirish"

install:
	pip install -r requirements.txt
	alembic upgrade head

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic revision --autogenerate -m "$(msg)"

upgrade:
	alembic upgrade head

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-rebuild:
	docker-compose down
	docker-compose build
	docker-compose up -d

test:
	pytest tests/

# EOF