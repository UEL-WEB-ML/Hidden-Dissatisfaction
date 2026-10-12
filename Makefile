.PHONY: install quality test format

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
