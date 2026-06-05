FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8004

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8004", "--workers", "4", "--threads", "2", "--timeout", "60", "--access-logfile", "-"]
