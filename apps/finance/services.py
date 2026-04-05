from apps.finance.models import FinancialRecord
from typing import Dict, Any
from rest_framework.exceptions import ValidationError

def create_financial_record(user, validated_data: Dict[str, Any]) -> FinancialRecord:
    """Isolates ledger insertion logic."""
    record = FinancialRecord(created_by=user, **validated_data)
    record.save()
    return record

def update_financial_record(record: FinancialRecord, validated_data: Dict[str, Any]) -> FinancialRecord:
    """Updates fields dynamically while protecting read-only properties."""
    for key, value in validated_data.items():
        setattr(record, key, value)
    record.save()
    return record

def soft_delete_record(record_id: str) -> None:
    """Physically protects ledger history while logical destroying access."""
    try:
        record = FinancialRecord.objects.get(id=record_id)
        record.is_deleted = True
        record.save(update_fields=['is_deleted'])
    except FinancialRecord.DoesNotExist:
        raise ValidationError({"detail": "Record not found or already deleted."})
