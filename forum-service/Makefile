.PHONY: install migrate test run

install:
	composer install

migrate:
	php artisan migrate

fresh:
	php artisan migrate:fresh --seed

test:
	php artisan test

run:
	php artisan serve --host=0.0.0.0 --port=8005

routes:
	php artisan route:list

shell:
	php artisan tinker
