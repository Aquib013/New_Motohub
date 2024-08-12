from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView

from svc.forms import PurchaseOrderItemForm
from svc.models import PurchaseOrderItem, PurchaseOrder


class PurchaseOrderItemCreateView(CreateView):
    model = PurchaseOrderItem
    form_class = PurchaseOrderItemForm
    template_name = 'purchase_order/purchase_order_item/add_item.html'

    def form_valid(self, form):
        purchase_order_id = self.kwargs.get('pk')
        purchase_order = PurchaseOrder.objects.get(pk=purchase_order_id)
        form.instance.purchase_order = purchase_order
        purchase_order.save()
        messages.success(self.request, "Item successfully Added in PO.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

    def get_success_url(self):
        purchase_order_id = self.kwargs.get('pk')
        return reverse_lazy('purchase-order-detail', kwargs={'pk': purchase_order_id})

    # to get purchase order number in template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_order_id = self.kwargs.get('pk')
        purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
        context['purchase_order'] = purchase_order
        context['form_media'] = self.form_class().media

        return context


class PurchaseOrderItemUpdateView(UpdateView):
    model = PurchaseOrderItem
    form_class = PurchaseOrderItemForm
    template_name = 'purchase_order/purchase_order_item/add_item.html'

    def form_valid(self, form):
        purchase_order_item = form.save()
        messages.success(self.request, "Item successfully updated in PO.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

    def get_success_url(self):
        purchase_order_id = self.object.purchase_order.pk
        return reverse_lazy('purchase-order-detail', kwargs={'pk': purchase_order_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['purchase_order'] = self.object.purchase_order
        context['form_media'] = self.form_class().media

        return context
