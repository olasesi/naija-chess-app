.PHONY: install migrate run test lint format shell seed

install:
	pip install -r requirements/development.txt

migrate:
	python manage.py migrate

run:
	python manage.py runserver 0.0.0.0:8008

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

seed:
	python manage.py seed_achievements

collectstatic:
	python manage.py collectstatic --noinput