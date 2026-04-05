from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal

from apps.users.models import Role
from apps.finance.models import FinancialRecord, RecordType

User = get_user_model()

class FinancialRecordAPIAndServicesTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='pw', role=Role.ADMIN)
        self.analyst = User.objects.create_user(username='analyst', password='pw', role=Role.ANALYST)
        self.viewer = User.objects.create_user(username='viewer', password='pw', role=Role.VIEWER)
        
        # Prefill base ledger entry created by the admin
        self.record1 = FinancialRecord.objects.create(
            amount=Decimal('150.50'),
            record_type=RecordType.INCOME,
            category='Software Services',
            date=date.today(),
            notes='Initial project income',
            created_by=self.admin
        )
        
        self.url = '/api/v1/records/'
        
    def authenticate(self, user):
        response = self.client.post('/api/v1/users/auth/token/', {
            'username': user.username,
            'password': 'pw'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_admin_can_create_record(self):
        self.authenticate(self.admin)
        payload = {
            "amount": "200.00",
            "record_type": RecordType.EXPENSE,
            "category": "Office Supplies",
            "date": "2026-04-01",
            "notes": "Pens and paper"
        }
        res = self.client.post(self.url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FinancialRecord.objects.count(), 2)

    def test_amount_must_be_positive_constraint(self):
        self.authenticate(self.admin)
        payload = {
            "amount": "-50.00", # Explicitly testing negative bounds logic
            "record_type": RecordType.EXPENSE,
            "category": "Penalties",
            "date": "2026-04-01"
        }
        res = self.client.post(self.url, payload, format='json')
        # DTO must catch it before DB
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analyst_can_read_but_cannot_create(self):
        self.authenticate(self.analyst)
        
        # Test read
        read_res = self.client.get(self.url)
        self.assertEqual(read_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(read_res.data), 1)
        
        # Test physical Create block (RBAC override)
        post_res = self.client.post(self.url, {"amount": "10", "record_type": "INCOME", "category": "A", "date": "2026-04-01"})
        self.assertEqual(post_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_is_totally_locked_out_of_records(self):
        self.authenticate(self.viewer)
        read_res = self.client.get(self.url)
        # Even reads are forbidden here. Dashboards are their only domain.
        self.assertEqual(read_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_soft_delete_mechanics_and_ghosting(self):
        self.authenticate(self.admin)
        delete_url = f"{self.url}{self.record1.id}/"
        
        # Execute soft DELETE request
        res = self.client.delete(delete_url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        
        # Test 1: Record is officially hidden from API fetches
        fetch_res = self.client.get(self.url)
        self.assertEqual(len(fetch_res.data), 0)
        
        # Test 2: Prove physical DB structure remains fully intact
        # using the hidden raw Manager we registered earlier for audit trails
        self.assertEqual(FinancialRecord.all_objects.count(), 1)
        db_raw_record = FinancialRecord.all_objects.first()
        self.assertTrue(db_raw_record.is_deleted)
