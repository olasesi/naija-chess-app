import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        errors = response.data
        message = "Request failed"
        if isinstance(errors, dict):
            message = errors.pop("detail", str(exc))
        elif isinstance(errors, list):
            message = str(errors[0]) if errors else str(exc)
        else:
            message = str(errors)
        response.data = {"success": False, "message": message, "errors": errors if isinstance(errors, dict) and errors else None}
    else:
        logger.exception("Unhandled exception: %s", exc)
        response = Response({"success": False, "message": "Internal server error"}, status=500)
    return response
