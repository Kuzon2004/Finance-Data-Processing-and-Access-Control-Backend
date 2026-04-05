from django.db import models
from django.db.models.functions import Coalesce, TruncMonth
from decimal import Decimal
from apps.finance.models import RecordType

def calculate_dashboard_summary(base_queryset) -> dict:
    """Takes a filtered FinancialRecord queryset and executes native SQL aggregations safely."""
    
    # 1. Base Aggregations (Income, Expenses, Net)
    aggregations = base_queryset.aggregate(
        total_income=Coalesce(
            models.Sum('amount', filter=models.Q(record_type=RecordType.INCOME)), 
            Decimal('0.00'),
            output_field=models.DecimalField()
        ),
        total_expenses=Coalesce(
            models.Sum('amount', filter=models.Q(record_type=RecordType.EXPENSE)), 
            Decimal('0.00'),
            output_field=models.DecimalField()
        )
    )

    income = aggregations['total_income']
    expenses = aggregations['total_expenses']
    net_balance = income - expenses

    # 2. Category-wise Totals
    category_totals = list(
        base_queryset.values('category')
        .annotate(total=models.Sum('amount'))
        .order_by('-total')
    )
    for cat in category_totals:
        cat['total'] = str(cat['total'])

    # 3. Monthly Trends
    monthly_trends = list(
        base_queryset.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(
            income=Coalesce(
                models.Sum('amount', filter=models.Q(record_type=RecordType.INCOME)), 
                Decimal('0.00'),
                output_field=models.DecimalField()
            ),
            expense=Coalesce(
                models.Sum('amount', filter=models.Q(record_type=RecordType.EXPENSE)), 
                Decimal('0.00'),
                output_field=models.DecimalField()
            )
        )
        .order_by('month')
    )
    for trend in monthly_trends:
        trend['month'] = trend['month'].strftime('%Y-%m') if trend['month'] else None
        trend['income'] = str(trend['income'])
        trend['expense'] = str(trend['expense'])

    # 4. Recent Activity (Last 5 transactions)
    recent_activity = list(
        base_queryset.order_by('-created_at')[:5]
        .values('id', 'amount', 'record_type', 'category', 'date')
    )
    for activity in recent_activity:
        activity['amount'] = str(activity['amount'])
        activity['id'] = str(activity['id'])
        activity['date'] = str(activity['date'])

    return {
        "total_income": str(income),
        "total_expenses": str(expenses),
        "net_balance": str(net_balance),
        "category_totals": category_totals,
        "monthly_trends": monthly_trends,
        "recent_activity": recent_activity
    }
