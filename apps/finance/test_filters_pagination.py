from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import date

from apps.users.models import Role
from apps.finance.models import FinancialRecord, RecordType

User = get_user_model()

class FinancialFilteringAndPaginationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin_filter', password='pw', role=Role.ADMIN)
        self.url = '/api/v1/records/'
        
        # Hydrate Database for exact match filtering
        FinancialRecord.objects.create(amount='10', record_type=RecordType.INCOME, category='API Sub', date='2026-04-01', created_by=self.admin)
        FinancialRecord.objects.create(amount='20', record_type=RecordType.INCOME, category='Consulting', date='2026-04-15', created_by=self.admin)
        FinancialRecord.objects.create(amount='50', record_type=RecordType.EXPENSE, category='AWS Hosting', date='2026-04-20', created_by=self.admin)
        
    def authenticate(self, user):
        response = self.client.post('/api/v1/users/auth/token/', {'username': user.username, 'password': 'pw'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_default_pagination_structure(self):
        self.authenticate(self.admin)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # DRF PageNumberPagination natively returns 'count', 'next', 'previous', 'results'
        self.assertIn('count', res.data)
        self.assertEqual(res.data['count'], 3)
        self.assertEqual(len(res.data['results']), 3)

    def test_filter_by_exact_record_type(self):
        self.authenticate(self.admin)
        res = self.client.get(f"{self.url}?record_type=EXPENSE")
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['category'], 'AWS Hosting')

    def test_filter_by_category_icontains(self):
        self.authenticate(self.admin)
        # Testing case-insensitive text match ('aws' should catch 'AWS Hosting')
        res = self.client.get(f"{self.url}?category=aws")
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['category'], 'AWS Hosting')

    def test_filter_by_date_range(self):
        self.authenticate(self.admin)
        # Fetch bound between 4-01 and 4-10
        res = self.client.get(f"{self.url}?start_date=2026-04-01&end_date=2026-04-10")
        self.assertEqual(res.data['count'], 1)
        self.assertEqual(res.data['results'][0]['category'], 'API Sub')

    def test_filter_invalid_date_throws_400(self):
        self.authenticate(self.admin)
        res = self.client.get(f"{self.url}?start_date=not-a-date")
        # django-filters inherently prevents DB crashes logic by enforcing validation
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
