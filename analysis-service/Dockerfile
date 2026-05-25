FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libmariadb-dev pkg-config stockfish \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ ./requirements/
RUN pip install --no-cache-dir --user -r requirements/production.txt

COPY . .

FROM python:3.12-slim AS production
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb-dev stockfish \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV STOCKFISH_PATH=/usr/games/stockfish

RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8002

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8002", "--workers", "2", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
