.PHONY: install quality test format db-up db-down db-logs

install:
	python -m pip install -e ".[ml,notebook,dev]"

quality:
	ruff check .
	black --check .
	mypy src tests
	pytest --cov=hidden_dissatisfaction --cov-report=term-missing

test:
	pytest

format:
	ruff check --fix .
	black .

db-up:
	docker compose up -d

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres
