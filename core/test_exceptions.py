from django.test import TestCase
from rest_framework.request import Request
from django.http import HttpRequest
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from core.exceptions import global_error_interceptor

class ExceptionHandlerTests(TestCase):
    def setUp(self):
        # We dummy out a context object just to satisfy DRF's handler expectations
        # A view context isn't strictly necessary to parse the raw exceptions conceptually
        self.context = {'view': None}

    def test_standard_drf_validation_error_formatting(self):
        # Simulate an API Input Serialization crash DTO
        exc = ValidationError({"amount": ["Must be greater than zero."]})
        response = global_error_interceptor(exc, self.context)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 400)
        self.assertEqual(response.data['error']['type'], 'ValidationError')
        # Structure payload is mapped natively to 'message' dictionary
        self.assertIn("amount", response.data['error']['message'])

    def test_rbac_permission_denied_formatting(self):
        # Simulate RBAC Engine Throwing a generic rejection
        exc = PermissionDenied("You do not have permission to perform this action.")
        response = global_error_interceptor(exc, self.context)
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error']['code'], 403)
        self.assertEqual(response.data['error']['type'], 'PermissionDenied')

    def test_database_integrity_error_hijacking(self):
        # Simulate a direct DB-level collision (e.g., trying to write duplicate Usernames manually)
        # Normally this yields a 500 error if untreated. Our handler upgrades it to 409 Conflict.
        exc = IntegrityError("UNIQUE constraint failed")
        response = global_error_interceptor(exc, self.context)
        
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['error']['code'], 409)

    def test_raw_unhandled_python_crash_hiding(self):
        # Explicit test proving that if a standard unhandled python KeyError breaks the code,
        # it is silently swallowed and obfuscated into a 500 JSON object rather than HTML.
        exc = KeyError("Critical internal DB reference missing")
        response = global_error_interceptor(exc, self.context)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data['error']['code'], 500)
        self.assertEqual(response.data['error']['message'], 'An unexpected system failure occurred.')
        # Ensure we didn't literally log the error message back to the dangerous client payload
        self.assertNotIn("Critical internal DB reference missing", str(response.data))
