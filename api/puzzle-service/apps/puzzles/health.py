"""JSON health check endpoint (replaces django-health-check, which renders HTML)."""
from django.db import connection
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        checks = {}

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            checks["database"] = "ok"
        except Exception:
            checks["database"] = "error"

        try:
            cache.set("__healthcheck__", "1", timeout=10)
            checks["cache"] = "ok" if cache.get("__healthcheck__") == "1" else "error"
        except Exception:
            checks["cache"] = "unavailable"

        healthy = checks.get("database") == "ok"
        return Response(
            {
                "status": "ok" if healthy else "degraded",
                "service": "puzzle-service",
                "version": "1.0.0",
                "checks": checks,
            },
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
