from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from apps.users.models import Role
from apps.users.services import create_system_user, toggle_user_status

User = get_user_model()

class UserServiceTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='password', role=Role.ADMIN)

    def test_create_system_user_success(self):
        user = create_system_user('new_analyst', 'securepass123', Role.ANALYST)
        self.assertEqual(user.username, 'new_analyst')
        self.assertEqual(user.role, Role.ANALYST)
        self.assertTrue(user.check_password('securepass123'))

    def test_create_system_user_duplicate(self):
        create_system_user('viewer', 'securepass123', Role.VIEWER)
        with self.assertRaises(ValidationError):
            create_system_user('viewer', 'securepass123', Role.VIEWER)

    def test_toggle_user_status_success(self):
        user = create_system_user('viewer', 'securepass123', Role.VIEWER)
        toggle_user_status(user.id, False, request_user=self.admin)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_toggle_self_admin_fails(self):
        with self.assertRaises(ValidationError):
            toggle_user_status(self.admin.id, False, request_user=self.admin)


class UserAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='password', role=Role.ADMIN)
        self.viewer = User.objects.create_user(username='viewer', password='password', role=Role.VIEWER)
        self.url = '/api/v1/users/'
        
    def authenticate(self, user):
        response = self.client.post('/api/v1/users/auth/token/', {
            'username': user.username,
            'password': 'password'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_admin_can_list_users(self):
        self.authenticate(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_viewer_cannot_list_users(self):
        self.authenticate(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_user(self):
        self.authenticate(self.admin)
        response = self.client.post(self.url, {
            'username': 'analyst1',
            'password': 'securepassword',
            'role': Role.ANALYST
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='analyst1').exists())

    def test_viewer_cannot_create_user(self):
        self.authenticate(self.viewer)
        response = self.client.post(self.url, {
            'username': 'analyst1',
            'password': 'securepassword',
            'role': Role.ANALYST
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_toggle_status(self):
        self.authenticate(self.admin)
        response = self.client.patch(f"{self.url}{self.viewer.id}/status/", {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.viewer.refresh_from_db()
        self.assertFalse(self.viewer.is_active)
