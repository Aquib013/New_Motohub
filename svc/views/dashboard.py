from django.utils import timezone
from django.utils.timezone import localdate
from django.views.generic import TemplateView

from svc.models import Item
from svc.views.insights import get_insights


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = localdate()

        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date and end_date:
            start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            # Default to today's date if no date range is selected
            start_date = end_date = today

        # Get insights
        insights = get_insights(start_date, end_date)

        low_stock_items = Item.objects.filter(item_quantity_in_stock__lt=1)

        # Update context with insights
        context.update(insights)
        context['low_stock_items'] = low_stock_items
        context['today'] = today
        context['start_date'] = start_date
        context['end_date'] = end_date

        return context
