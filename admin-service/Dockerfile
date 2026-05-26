FROM php:8.2-cli-alpine

ENV APP_ENV=production \
    APP_DEBUG=false \
    DB_CONNECTION=mysql \
    DB_HOST=mysql-admin \
    DB_PORT=3306 \
    DB_DATABASE=gameplatform_admin \
    DB_USERNAME=root \
    DB_PASSWORD=rootpassword

RUN apk add --no-cache mysql-client mysql-dev libzip-dev oniguruma-dev \
    && docker-php-ext-install pdo_mysql mbstring zip

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

COPY . .

RUN composer install --no-dev --no-interaction --optimize-autoloader \
    && chmod -R 777 storage bootstrap/cache \
    && php artisan key:generate

EXPOSE 8006

CMD php artisan serve --host=0.0.0.0 --port=8006
