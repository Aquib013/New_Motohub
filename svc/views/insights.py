from django.db.models import Sum
from datetime import timedelta

from django.utils import timezone

from svc.models import Job, Expense, Service, JobItem, PurchaseOrder


def get_insights(date=None, period='daily'):
    if period == 'daily':
        start_date = end_date = timezone.localtime(timezone.now()).date()
    elif period == 'weekly':
        start_date = date - timedelta(days=date.weekday())  # Start of the week
        end_date = start_date + timedelta(days=6)  # End of the week
    elif period == 'monthly':
        start_date = date.replace(day=1)  # Start of the month
        next_month = start_date.replace(month=date.month % 12 + 1, day=1)
        end_date = next_month - timedelta(days=1)  # End of the month

    machining_revenue = Service.objects.filter(
        service_type='Machining',
        job__job_completion_time__date__range=[start_date, end_date]  # NOQA
    ).aggregate(Sum('service_cost'))['service_cost__sum'] or 0

    workshop_revenue = Service.objects.filter(
        service_type='Workshop',
        job__job_completion_time__date__range=[start_date, end_date]
    ).aggregate(Sum('service_cost'))['service_cost__sum'] or 0

    total_service_revenue = Job.objects.filter(
        job_completion_time__date__range=[start_date, end_date]
    ).aggregate(Sum('total_service_cost'))['total_service_cost__sum'] or 0

    total_item_revenue = Job.objects.filter(
        job_completion_time__date__range=[start_date, end_date]
    ).aggregate(Sum('total_item_cost'))['total_item_cost__sum'] or 0

    total_profit_by_item = sum(
        (job_item.item_unit_price - job_item.item.cost_price) * job_item.item_quantity
        for job_item in JobItem.objects.filter(job__job_completion_time__date__range=[start_date, end_date])
    )

    total_revenue = Job.objects.filter(
        job_completion_time__date__range=[start_date, end_date]
    ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    total_expense = Expense.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    item_purchased = PurchaseOrder.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).aggregate(Sum('po_amount'))['po_amount__sum'] or 0

    total_income = total_revenue - total_expense

    return {
        'machining_revenue': machining_revenue,
        'workshop_revenue': workshop_revenue,
        'total_service_revenue': total_service_revenue,
        'total_item_revenue': total_item_revenue,
        'total_profit_by_item': total_profit_by_item,
        "item_purchased": item_purchased,
        'total_revenue': total_revenue,
        'total_expense': total_expense,
        'total_income': total_income,
        'start_date': start_date,
        'end_date': end_date,
    }
