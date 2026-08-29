.PHONY: up down build seed dev-backend dev-frontend test

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

seed:
	docker compose exec backend python -m app.seed.seed_demo_data

logs:
	docker compose logs -f

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest tests/ -v

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

setup:
	cp .env.example .env
	@echo "Edit .env with your settings, then run: make up"
