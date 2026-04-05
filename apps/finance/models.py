import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from apps.users.models import User
from apps.finance.managers import ActiveRecordManager

class RecordType(models.TextChoices):
    INCOME = 'INCOME', 'Income'
    EXPENSE = 'EXPENSE', 'Expense'

class FinancialRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    record_type = models.CharField(max_length=10, choices=RecordType.choices)
    category = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)
    notes = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='financial_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Attach the custom manager so deleted records are ghosted physically
    objects = ActiveRecordManager()
    all_objects = models.Manager() # Keep for admin/audit purposes raw access

    class Meta:
        db_table = 'financial_records'
        indexes = [
            models.Index(fields=['date', 'record_type', 'category']),
        ]
