from django.utils import timezone
from django.views.generic import TemplateView

from svc.models import Item
from svc.views.insights import get_insights


class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        period = self.request.GET.get('period', 'daily')
        selected_date = self.request.GET.get('date')

        if selected_date:
            selected_date = timezone.datetime.strptime(selected_date, "%Y-%m-%d").date()
        else:
            # Default to current date if no date is selected
            selected_date = today

        # Get insights
        insights = get_insights(selected_date, period)

        low_stock_items = Item.objects.filter(item_quantity_in_stock__lt=1)

        # Update context with insights
        context.update(insights)
        context['low_stock_items'] = low_stock_items
        context['today'] = timezone.now().date()
        context['selected_date'] = selected_date
        context['period'] = period

        return context
