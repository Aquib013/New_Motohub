from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, DeleteView, UpdateView, DetailView

from svc.forms import VendorForm
from svc.models import Vendor, PurchaseOrder, Expense


class VendorCreateView(CreateView):
    model = Vendor
    template_name = "vendor/create_vendor.html"
    form_class = VendorForm
    success_url = reverse_lazy("vendors")


class VendorListView(ListView):
    model = Vendor
    template_name = "vendor/vendors_list.html"
    context_object_name = "vendors"
    ordering = ['-created_at']


class VendorUpdateView(UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = "vendor/create_vendor.html"
    success_url = reverse_lazy("vendors")


class VendorDeleteView(DeleteView):
    model = Vendor
    template_name = "vendor/vendor_confirm_delete.html"
    success_url = reverse_lazy("vendors")


class VendorPaymentHistoryView(DetailView):
    model = Vendor
    template_name = 'vendor/vendor_payment_history.html'
    context_object_name = 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_object()
        # Ordering the related payments by created_at
        payments = Expense.objects.filter(expense_type="Vendor Payment", vendor=vendor).order_by('-created_at')
        context['payments'] = payments
        return context


class VendorPurchaseOrdersView(DetailView):
    model = Vendor
    template_name = "vendor/vendor_pos.html"
    context_object_name = "vendor"
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_object()
        # Ordering the related purchase orders by created_at
        purchase_orders = vendor.purchase_orders.all().order_by('-created_at')
        context['purchase_orders'] = purchase_orders
        return context


class VendorPurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'vendor/vendor_po_detail.html'
    context_object_name = "po"

    def get_object(self, queryset=None):
        vendor_id = self.kwargs.get('vendor_pk')
        po_id = self.kwargs.get('po_pk')
        return get_object_or_404(PurchaseOrder, vendor__id=vendor_id, id=po_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendor'] = self.object.vendor
        context['po_items'] = self.object.purchase_order_item.all()
        return context
