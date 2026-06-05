from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [
    "django_extensions",
]

# Log to console only in development
LOGGING["handlers"] = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "verbose",
    },
}
LOGGING["root"]["handlers"] = ["console"]
LOGGING["root"]["level"] = "DEBUG"
