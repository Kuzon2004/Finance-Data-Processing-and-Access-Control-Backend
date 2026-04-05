from rest_framework.permissions import BasePermission
from apps.users.models import Role

class IsAuthenticatedAndActive(BasePermission):
    """Base check to ensure we only process active, logged-in JWTs."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)

class IsAdminRole(IsAuthenticatedAndActive):
    """Allows full mutation overrides (Users, Ledgers)."""
    def has_permission(self, request, view):
        is_valid_base = super().has_permission(request, view)
        return is_valid_base and request.user.role == Role.ADMIN

class IsAnalystOrAdmin(IsAuthenticatedAndActive):
    """Allows granular ledger reads."""
    def has_permission(self, request, view):
        is_valid_base = super().has_permission(request, view)
        return is_valid_base and request.user.role in [Role.ADMIN, Role.ANALYST]

class IsViewerOrHigher(IsAuthenticatedAndActive):
    """Allows dashboard aggregation reads (Baseline internal access)."""
    def has_permission(self, request, view):
        is_valid_base = super().has_permission(request, view)
        return is_valid_base and request.user.role in [Role.ADMIN, Role.ANALYST, Role.VIEWER]
