.PHONY: help install migrate test lint format dev

help:
	@echo "Commands:"
	@echo "  make install     Install dependencies"
	@echo "  make migrate     Run migrations"
	@echo "  make test        Run tests"
	@echo "  make lint        Run ruff linting"
	@echo "  make format      Run black + isort"
	@echo "  make dev         Start dev server"
	@echo "  make shell       Django shell"

install:
	pip install -r requirements/development.txt
	python manage.py check

migrate:
	python manage.py makemigrations
	python manage.py migrate

test:
	pytest --cov=apps --cov-report=term --cov-report=html --reuse-db -v

lint:
	ruff check apps/ common/ config/ --fix

format:
	black apps/ common/ config/
	isort apps/ common/ config/

dev:
	python manage.py runserver 0.0.0.0:8000

shell:
	python manage.py shell_plus
