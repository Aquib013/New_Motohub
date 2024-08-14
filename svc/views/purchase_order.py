from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from svc.models import PurchaseOrder
from svc.forms import PurchaseOrderForm


class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchase_order/purchase_order_list.html'
    context_object_name = "purchase_orders"
    ordering = ['-created_at']


class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'purchase_order/purchase_order_form.html'
    success_url = reverse_lazy('purchase-orders')

    def form_valid(self, form):
        purchase_order = form.save(commit=False)
        purchase_order.save()
        messages.success(self.request, "Purchase Order created successfully.")
        return super().form_valid(form)


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
