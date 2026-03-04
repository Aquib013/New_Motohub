from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from svc.models import Job, Expense, Service, JobItem, PurchaseOrder


def get_insights(start_date=None, end_date=None):
    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = end_date = today

    # Base queryset: jobs in date range that have been paid
    paid_jobs = Job.objects.filter(
        job_date__range=[start_date, end_date],
        paid_amount__gt=0
    )

    # Aggregate job-level totals in a single query
    job_totals = paid_jobs.aggregate(
        total_service_revenue=Coalesce(Sum('total_service_cost'), 0, output_field=DecimalField()),
        total_item_revenue=Coalesce(Sum('total_item_cost'), 0, output_field=DecimalField()),
        total_revenue=Coalesce(Sum('paid_amount'), 0, output_field=DecimalField()),
    )

    # Service type breakdown (2 queries → could also be 1 with conditional aggregation)
    service_revenue = Service.objects.filter(
        job__in=paid_jobs
    ).values('service_type').annotate(
        revenue=Coalesce(Sum('service_cost'), 0, output_field=DecimalField())
    )
    service_revenue_map = {item['service_type']: item['revenue'] for item in service_revenue}

    # Item profit at DB level instead of Python loop
    total_profit_by_item = JobItem.objects.filter(
        job__in=paid_jobs
    ).aggregate(
        profit=Coalesce(
            Sum(
                (F('item_unit_price') - Coalesce(F('item__cost_price'), 0)) * F('item_quantity'),
                output_field=DecimalField()
            ), 0, output_field=DecimalField()
        )
    )['profit']

    # Expenses and purchases
    total_expense = Expense.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).aggregate(total=Coalesce(Sum('amount'), 0, output_field=DecimalField()))['total']

    item_purchased = PurchaseOrder.objects.filter(
        po_date__range=[start_date, end_date]
    ).aggregate(total=Coalesce(Sum('po_amount'), 0, output_field=DecimalField()))['total']

    total_revenue = job_totals['total_revenue']
    total_income = total_revenue - total_expense

    return {
        'machining_revenue': service_revenue_map.get('Machining', 0),
        'workshop_revenue': service_revenue_map.get('Workshop', 0),
        'total_service_revenue': job_totals['total_service_revenue'],
        'total_item_revenue': job_totals['total_item_revenue'],
        'total_profit_by_item': total_profit_by_item,
        'item_purchased': item_purchased,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'total_income': total_income,
        'start_date': start_date,
        'end_date': end_date,
    }