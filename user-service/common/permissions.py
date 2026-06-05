from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Allow access only to the resource owner."""

    def has_object_permission(self, request, view, obj):
        user_id = getattr(request.user, "id", None)
        obj_user_id = getattr(obj, "userId", None) or getattr(obj, "user_id", None)
        return str(user_id) == str(obj_user_id)


class HasRole(BasePermission):
    """Allow access only to users with specified roles."""

    def __init__(self, *roles):
        self.roles = roles

    def has_permission(self, request, view):
        role = getattr(request.user, "role", None)
        return role in self.roles


class IsAdmin(HasRole):
    def __init__(self):
        super().__init__("ADMIN", "MODERATOR")


class ReadOnly(BasePermission):
    """Allow read-only access (GET, HEAD, OPTIONS)."""

    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")
