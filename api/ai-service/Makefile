.PHONY: help install migrate seed makemigrations test shell

PYTHON ?= python

help:
	@echo "dev - run locally, test - run tests, migrate - apply migrations"

install:
	$(PYTHON) -m pip install -r requirements/development.txt

makemigrations:
	$(PYTHON) manage.py makemigrations

migrate:
	$(PYTHON) manage.py migrate

test:
	$(PYTHON) -m pytest

shell:
	$(PYTHON) manage.py shell