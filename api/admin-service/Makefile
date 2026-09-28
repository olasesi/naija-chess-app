.PHONY: help test migrate fresh shell

help:
	@echo 'Admin Service - Laravel'
	@echo '  make test     - Run tests'
	@echo '  make migrate  - Run migrations'
	@echo '  make fresh    - Fresh migrate + seed'
	@echo '  make shell    - Open artisan tinker'

test:
	php artisan test

migrate:
	php artisan migrate

fresh:
	php artisan migrate:fresh --seed

shell:
	php artisan tinker
