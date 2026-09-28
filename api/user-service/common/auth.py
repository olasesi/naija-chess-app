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
        user_id = request.headers.get("X-User-Id")
        user_email = request.headers.get("X-User-Email")
        user_role = request.headers.get("X-User-Role")

        if user_id and user_email and user_role:
            return AuthUser(user_id, user_email, user_role), None

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

        return AuthUser(
            payload.get("sub"),
            payload.get("email"),
            payload.get("role", "PLAYER"),
        ), None
