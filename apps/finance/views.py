from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.finance.models import FinancialRecord
from apps.finance.serializers import FinancialRecordInputSerializer, FinancialRecordOutputSerializer
from apps.finance.services import create_financial_record, update_financial_record, soft_delete_record
from apps.finance.filters import FinancialRecordFilter
from core.permissions import IsAdminRole, IsAnalystOrAdmin

class FinancialRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Financial Ledgers.
    Dynamically maps HTTP verbs against the custom RBAC engine core components.
    """
    queryset = FinancialRecord.objects.all().order_by('-date')
    filterset_class = FinancialRecordFilter

    def get_permissions(self):
        """Dynamic Policy Router"""
        if self.action in ['retrieve', 'list']:
            permission_classes = [IsAnalystOrAdmin]
        else:
            # POST, PUT, PATCH, DELETE are locked strictly to Admins
            permission_classes = [IsAdminRole]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FinancialRecordInputSerializer
        return FinancialRecordOutputSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = create_financial_record(user=request.user, validated_data=serializer.validated_data)
        out_serializer = FinancialRecordOutputSerializer(record)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        record = update_financial_record(instance, serializer.validated_data)
        out_serializer = FinancialRecordOutputSerializer(record)
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        # Prevent physical DESTROY. Override with Soft Delete service.
        instance = self.get_object()
        soft_delete_record(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
