import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
logger = logging.getLogger(__name__)

def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        errors = response.data
        msg = "Request failed"
        if isinstance(errors, dict): msg = errors.pop("detail", str(exc))
        elif isinstance(errors, list): msg = str(errors[0]) if errors else str(exc)
        else: msg = str(errors)
        response.data = {"success": False, "message": msg, "errors": errors if isinstance(errors, dict) and errors else None}
    else:
        logger.exception("Unhandled: %s", exc)
        response = Response({"success": False, "message": "Internal server error"}, status=500)
    return response
