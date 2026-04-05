from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from apps.users.models import Role
from core.permissions import (
    IsAuthenticatedAndActive, 
    IsAdminRole, 
    IsAnalystOrAdmin, 
    IsViewerOrHigher
)

User = get_user_model()

class MockView:
    """Mock ViewSet for testing DRF Permissions natively"""
    pass

class RBACEngineTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = MockView()
        
        # Matrix of users representing all logical access states
        self.admin = User.objects.create_user(username='admin', password='pw', role=Role.ADMIN, is_active=True)
        self.analyst = User.objects.create_user(username='analyst', password='pw', role=Role.ANALYST, is_active=True)
        self.viewer = User.objects.create_user(username='viewer', password='pw', role=Role.VIEWER, is_active=True)
        
        # Edge Case users
        self.inactive_admin = User.objects.create_user(username='dead_admin', password='pw', role=Role.ADMIN, is_active=False)
        self.unauthenticated_user = None

    def _get_request_for_user(self, user):
        request = self.factory.get('/')
        request.user = user
        return request

    def test_base_authentication_and_active_gate(self):
        permission = IsAuthenticatedAndActive()
        
        # Active authenticated users should pass
        self.assertTrue(permission.has_permission(self._get_request_for_user(self.admin), self.view))
        
        # Edge cases should fail inherently
        self.assertFalse(permission.has_permission(self._get_request_for_user(self.inactive_admin), self.view))
        # Abstracting unauthenticated user simulating DRF AnonymousUser
        request = self._get_request_for_user(self.unauthenticated_user)
        request.user = type('Anonymous', (), {'is_authenticated': False, 'is_active': False})() # Standard DRF anonymous wrapper
        self.assertFalse(permission.has_permission(request, self.view))

    def test_is_admin_role_enforcement(self):
        permission = IsAdminRole()
        
        self.assertTrue(permission.has_permission(self._get_request_for_user(self.admin), self.view))
        
        self.assertFalse(permission.has_permission(self._get_request_for_user(self.analyst), self.view))
        self.assertFalse(permission.has_permission(self._get_request_for_user(self.viewer), self.view))
        self.assertFalse(permission.has_permission(self._get_request_for_user(self.inactive_admin), self.view))

    def test_is_analyst_or_admin_enforcement(self):
        permission = IsAnalystOrAdmin()
        
        self.assertTrue(permission.has_permission(self._get_request_for_user(self.admin), self.view))
        self.assertTrue(permission.has_permission(self._get_request_for_user(self.analyst), self.view))
        
        self.assertFalse(permission.has_permission(self._get_request_for_user(self.viewer), self.view))
        self.assertFalse(permission.has_permission(self._get_request_for_user(self.inactive_admin), self.view))

    def test_is_viewer_or_higher_enforcement(self):
        permission = IsViewerOrHigher()
        
        self.assertTrue(permission.has_permission(self._get_request_for_user(self.admin), self.view))
        self.assertTrue(permission.has_permission(self._get_request_for_user(self.analyst), self.view))
        self.assertTrue(permission.has_permission(self._get_request_for_user(self.viewer), self.view))
        
        # Even a viewer should be physically blocked if their account is deactivated
        self.assertFalse(permission.has_permission(self._get_request_for_user(self.inactive_admin), self.view))
