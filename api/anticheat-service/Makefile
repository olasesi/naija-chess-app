.PHONY: install migrate run test lint format shell

install:
	pip install -r requirements/development.txt

migrate:
	python manage.py migrate

run:
	python manage.py runserver 0.0.0.0:8009

test:
	pytest

lint:
	ruff check apps/ config/ common/
	black --check apps/ config/ common/
	isort --check-only apps/ config/ common/

format:
	black apps/ config/ common/
	isort apps/ config/ common/

shell:
	python manage.py shell

collectstatic:
	python manage.py collectstatic --noinput