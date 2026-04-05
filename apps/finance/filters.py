import django_filters
from apps.finance.models import FinancialRecord, RecordType

class FinancialRecordFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    category = django_filters.CharFilter(lookup_expr='icontains')
    record_type = django_filters.ChoiceFilter(choices=RecordType.choices)

    class Meta:
        model = FinancialRecord
        fields = ['record_type', 'category']
