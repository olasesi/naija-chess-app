import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class GatewayJWTAuthentication(BaseAuthentication):
    """
    Authenticate using either:
    1. Gateway-forwarded headers (X-User-Id, X-User-Email, X-User-Role) — internal trust
    2. Direct JWT from Authorization header — for direct access / testing
    """

    def authenticate(self, request):
        user_id = request.headers.get("X-User-Id")
        user_email = request.headers.get("X-User-Email")
        user_role = request.headers.get("X-User-Role")

        if user_id and user_email and user_role:
            return self._build_user(user_id, user_email, user_role), None

        return self._authenticate_jwt(request)

    def _authenticate_jwt(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Access token required")

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_ACCESS_SECRET,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Access token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid access token")

        return self._build_user(
            payload.get("sub"),
            payload.get("email"),
            payload.get("role", "PLAYER"),
        ), None

    def _build_user(self, user_id, email, role):
        from django.contrib.auth.models import AnonymousUser, User

        user = AnonymousUser()
        user.id = user_id
        user.pk = user_id
        user.email = email
        user.role = role
        user.is_authenticated = True
        return user
