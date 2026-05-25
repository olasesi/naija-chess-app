import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class AuthUser:
    def __init__(self, user_id, email, role):
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.role = role
        self.is_authenticated = True

    def __str__(self):
        return self.id


class GatewayJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        uid = request.headers.get("X-User-Id")
        email = request.headers.get("X-User-Email")
        role = request.headers.get("X-User-Role")
        if uid and email and role:
            return AuthUser(uid, email, role), None
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
        return AuthUser(payload.get("sub"), payload.get("email"), payload.get("role", "PLAYER")), None
