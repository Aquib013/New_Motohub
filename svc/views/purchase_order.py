from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import localdate
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from svc.models import PurchaseOrder
from svc.forms import PurchaseOrderForm


class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchase_order/purchase_order_list.html'
    context_object_name = "purchase_orders"
    ordering = ['-created_at']

    def get_queryset(self):
        selected_date = self.request.GET.get('date')
        if selected_date:
            return PurchaseOrder.objects.filter(po_date=selected_date).order_by('po_number')
        else:
            return PurchaseOrder.objects.filter(po_date=localdate()).order_by('po_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_date'] = self.request.GET.get('date', localdate().isoformat())
        return context


class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchase_order/purchase_order_form.html'

    def form_valid(self, form):
        self.object = form.save()  # NOQA
        messages.success(self.request, "Purchase Order created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('purchase-order-detail', kwargs={'pk': self.object.pk})


class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'purchase_order/purchase_order_detail.html'


class PurchaseOrderUpdateView(UpdateView):
    model = PurchaseOrder
    fields = ['vendor']
    template_name = 'purchase_order/purchase_order_form.html'
    success_url = reverse_lazy('purchase-orders')


class PurchaseOrderDeleteView(DeleteView):
    model = PurchaseOrder
    template_name = 'purchase_order/purchase_order_confirm_delete.html'
    success_url = reverse_lazy('purchase-orders')
