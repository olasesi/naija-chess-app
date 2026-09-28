.PHONY: install migrate run test lint

install:
	pip install -r requirements/development.txt

migrate:
	python manage.py migrate

run:
	python manage.py runserver 0.0.0.0:8004

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
	python manage.py shell_plus

load_puzzles:
	python manage.py load_puzzles

seed_daily:
	python manage.py set_daily_puzzle

load_puzzles_and_seed:
	python manage.py load_puzzles
	python manage.py set_daily_puzzle

collectstatic:
	python manage.py collectstatic --noinput
