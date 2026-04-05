from rest_framework import serializers
from apps.finance.models import FinancialRecord, RecordType

class FinancialRecordOutputSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = FinancialRecord
        fields = ['id', 'amount', 'record_type', 'category', 'date', 'notes', 'created_by_username', 'created_at']
        read_only_fields = fields

class FinancialRecordInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialRecord
        fields = ['amount', 'record_type', 'category', 'date', 'notes']
        
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
