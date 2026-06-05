import os
from pathlib import Path
import pymysql
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

DJANGO_APPS = [
    "django.contrib.admin", "django.contrib.auth",
    "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "rest_framework", "corsheaders", "drf_spectacular",
    "health_check", "health_check.db", "health_check.cache",
]
LOCAL_APPS = ["apps.analysis", "apps.openings"]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    import re
    m = re.match(r"mysql://(.+):(.+)@(.+):(\d+)/(.+)", DATABASE_URL)
    if m:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": m.group(5), "USER": m.group(1),
                "PASSWORD": m.group(2), "HOST": m.group(3),
                "PORT": m.group(4),
                "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
                "CONN_MAX_AGE": 60,
            }
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "gameplatform_analysis"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", "rootpassword"),
            "HOST": os.getenv("DB_HOST", "localhost"),
            "PORT": os.getenv("DB_PORT", "3310"),
            "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
            "CONN_MAX_AGE": 60,
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/5"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "analysis",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("common.auth.GatewayJWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": ("common.renderers.APIJSONRenderer", "rest_framework.renderers.BrowsableAPIRenderer"),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
}
JWT_ACCESS_SECRET = os.getenv("JWT_ACCESS_SECRET", "change-me")

SPECTACULAR_SETTINGS = {
    "TITLE": "Chess Platform - Analysis Service",
    "DESCRIPTION": "Stockfish-powered game analysis, position evaluation, opening explorer",
    "VERSION": "1.0.0",
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/6")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/5")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# Stockfish
STOCKFISH_PATH = os.getenv("STOCKFISH_PATH", "/usr/games/stockfish")
STOCKFISH_HASH_SIZE = int(os.getenv("STOCKFISH_HASH_SIZE", "512"))
STOCKFISH_THREADS = int(os.getenv("STOCKFISH_THREADS", "2"))

# Analysis defaults
ANALYSIS_QUICK_DEPTH = 12
ANALYSIS_NORMAL_DEPTH = 18
ANALYSIS_DEEP_DEPTH = 24

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "analysis-service.log",
            "maxBytes": 10485760, "backupCount": 5, "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
}
