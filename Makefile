.PHONY: migrate rollback migration shell db-shell logs build down up

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up -d --build

logs:
	docker logs -f chatbot_api

migrate:
	docker exec -it chatbot_api alembic upgrade head

rollback:
	docker exec -it chatbot_api alembic downgrade -1

migration:
	docker exec -it chatbot_api alembic revision --autogenerate -m "$(msg)"

history:
	docker exec -it chatbot_api alembic history

current:
	docker exec -it chatbot_api alembic current

shell:
	docker exec -it chatbot_api bash

db-shell:
	docker exec -it chatbot_db psql -U chatbot_db -d chatbot_db


test:
	docker exec -it chatbot_api pytest -v

test-cov:
	docker exec -it chatbot_api pytest --cov=. --cov-report=term-missing

test-fast:
	docker exec -it chatbot_api pytest -x    