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

test_tournament:
	python manage.py create_test_tournament --players 8 --rounds 5

collectstatic:
	python manage.py collectstatic --noinput
