from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.finance.views import FinancialRecordViewSet

router = DefaultRouter()
router.register(r'', FinancialRecordViewSet, basename='records')

urlpatterns = [
    path('', include(router.urls)),
]
