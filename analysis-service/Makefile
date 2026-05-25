.PHONY: help install migrate test lint format dev openings

help:
	@echo "Commands:"
	@echo "  make install     Install dependencies"
	@echo "  make migrate     Run migrations"
	@echo "  make test        Run tests (skip stockfish)"
	@echo "  make test-all    Run all tests (requires stockfish)"
	@echo "  make lint        Run ruff"
	@echo "  make format      Run black + isort"
	@echo "  make dev         Start dev server"
	@echo "  make openings    Load ECO openings"

install:
	pip install -r requirements/development.txt
	python manage.py check

migrate:
	python manage.py makemigrations
	python manage.py migrate

test:
	pytest -m "not stockfish" --cov=apps --cov-report=term --reuse-db -v

test-all:
	pytest --cov=apps --cov-report=term --reuse-db -v

lint:
	ruff check apps/ common/ config/ --fix

format:
	black apps/ common/ config/
	isort apps/ common/ config/

dev:
	python manage.py runserver 0.0.0.0:8002

openings:
	python manage.py load_openings
