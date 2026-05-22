import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class GatewayJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        user_id = request.headers.get("X-User-Id")
        user_email = request.headers.get("X-User-Email")
        user_role = request.headers.get("X-User-Role")

        if user_id and user_email and user_role:
            return self._build_user(user_id, user_email, user_role), None

        return self._authenticate_jwt(request)

    def _authenticate_jwt(self, request):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise AuthenticationFailed("Token required")
        token = auth.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid token")
        return self._build_user(payload.get("sub"), payload.get("email"), payload.get("role", "PLAYER")), None

    def _build_user(self, user_id, email, role):
        from django.contrib.auth.models import AnonymousUser
        u = AnonymousUser()
        u.id = user_id
        u.pk = user_id
        u.email = email
        u.role = role
        u.is_authenticated = True
        return u
