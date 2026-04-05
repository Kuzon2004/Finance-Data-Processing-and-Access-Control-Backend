from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.users.models import Role
from apps.finance.models import FinancialRecord, RecordType

User = get_user_model()

class DashboardAggregationTests(APITestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username='dashboard_viewer', password='pw', role=Role.VIEWER)
        self.url = '/api/v1/dashboard/summary/'
        
        # Hydrate Base Database State
        FinancialRecord.objects.create(amount=Decimal('500.00'), record_type=RecordType.INCOME, category='Consulting', date='2026-04-01', created_by=self.viewer)
        FinancialRecord.objects.create(amount=Decimal('500.00'), record_type=RecordType.INCOME, category='Bonus', date='2026-04-02', created_by=self.viewer)
        FinancialRecord.objects.create(amount=Decimal('250.00'), record_type=RecordType.EXPENSE, category='Software', date='2026-04-03', created_by=self.viewer)
        
        # Soft-deleted record (Should mathematically be totally ignored!)
        # Explicit test for the ghosting mechanism inside aggregates.
        deleted = FinancialRecord.objects.create(amount=Decimal('9999.00'), record_type=RecordType.INCOME, category='Ghost', date='2026-04-03', created_by=self.viewer)
        deleted.is_deleted = True
        deleted.save()

    def authenticate(self, user):
        response = self.client.post('/api/v1/users/auth/token/', {'username': user.username, 'password': 'pw'})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_mathematical_aggregation_core(self):
        """Proves base calculation logic functions securely avoiding ghosted entries"""
        self.authenticate(self.viewer)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # Total Income = 500 + 500 = 1000.  (The 9999 is ignored)
        # Total Expense = 250
        # Net Balance = 750
        
        self.assertEqual(res.data['total_income'], "1000.00")
        self.assertEqual(res.data['total_expenses'], "250.00")
        self.assertEqual(res.data['net_balance'], "750.00")

    def test_mathematical_filtering_inheritance(self):
        """Proves dashboard accurately respects the django-filters passed via bounds."""
        self.authenticate(self.viewer)
        # Only query records exactly up to April 2nd. 
        # This inherently excludes the 250 EXPENSE on the 3rd.
        res = self.client.get(f"{self.url}?end_date=2026-04-02")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        self.assertEqual(res.data['total_income'], "1000.00")
        self.assertEqual(res.data['total_expenses'], "0.00")
        self.assertEqual(res.data['net_balance'], "1000.00")

    def test_null_coalesce_safeguard_for_empty_queries(self):
        """Proves that a completely filtered or empty database doesn't crash the Decimal cast via NULL bounds"""
        self.authenticate(self.viewer)
        res = self.client.get(f"{self.url}?start_date=2099-01-01") # Forces mathematically 0 rows
        
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_income'], "0.00")
        self.assertEqual(res.data['total_expenses'], "0.00")
        self.assertEqual(res.data['net_balance'], "0.00")
