from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend

from apps.finance.models import FinancialRecord
from apps.finance.filters import FinancialRecordFilter
from apps.dashboard.services import calculate_dashboard_summary
from core.permissions import IsViewerOrHigher

class DashboardSummaryView(APIView):
    """
    Computes real-time aggregation mathematics exclusively over the active ledgers.
    Inherits filtering schemas to allow dynamic timeline parsing.
    """
    permission_classes = [IsViewerOrHigher]
    filter_backends = [DjangoFilterBackend]
    filterset_class = FinancialRecordFilter

    def get_queryset(self):
        """Bind base active ledger."""
        return FinancialRecord.objects.all()

    def get(self, request, *args, **kwargs):
        # Instantiate DjangoFilterBackend safely to process URL Query Params
        queryset = self.get_queryset()
        
        # Apply strict query validations to restrict math bounds
        filter_backend = self.filter_backends[0]()
        filtered_queryset = filter_backend.filter_queryset(request, queryset, self)
        
        # Execute mathematical core
        summary_data = calculate_dashboard_summary(filtered_queryset)
        
        return Response(summary_data, status=status.HTTP_200_OK)
