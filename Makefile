PYTEST ?= python -m pytest

.PHONY: backend-test backend-lint backend-format frontend-build backend-run worker-run beat-run migrate seed docker-up docker-down

backend-test:
	cd backend && $(PYTEST) tests -q

backend-lint:
	cd backend && python -m ruff check app tests

backend-format:
	cd backend && python -m ruff format app tests

frontend-build:
	cd frontend && npm run build

backend-run:
	cd backend && python -m uvicorn app.main:app --reload

worker-run:
	cd backend && python -m celery -A app.workers.celery_app.celery_app worker --loglevel=info --queues=default,webhooks,sync,maintenance,messages,comments,posts

beat-run:
	cd backend && python -m celery -A app.workers.celery_app.celery_app beat --loglevel=info

migrate:
	cd backend && python -m alembic upgrade head

seed:
	cd backend && python scripts/seed_local_data.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down
