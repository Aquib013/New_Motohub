from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DeleteView, UpdateView, DetailView

from svc.forms import VendorForm
from svc.models import Vendor, Expense


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


class VendorHistoryView(DetailView):
    model = Vendor
    template_name = 'vendor/vendor_history.html'
    context_object_name = 'vendor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vendor = self.get_object()

        purchase_orders = (
            vendor.purchase_orders
            .prefetch_related('purchase_order_item__item')
            .order_by('-po_date')
        )
        payments = (
            Expense.objects
            .filter(expense_type="Vendor Payment", vendor=vendor)
            .order_by('-created_at')
        )

        context['purchase_orders'] = purchase_orders
        context['payments'] = payments
        context['total_po_amount'] = purchase_orders.aggregate(total=Sum('po_amount'))['total'] or 0
        context['total_paid'] = payments.aggregate(total=Sum('amount'))['total'] or 0
        return context


class VendorAddPaymentView(CreateView):
    model = Expense
    fields = ['amount', 'comment']

    def form_valid(self, form):
        vendor = get_object_or_404(Vendor, pk=self.kwargs['pk'])
        expense = form.save(commit=False)
        expense.expense_type = "Vendor Payment"
        expense.vendor = vendor
        expense.expense_title = f"Payment to {vendor.firm_name}"
        expense.save()
        messages.success(self.request, f"Payment of ₹{expense.amount} recorded successfully.")
        return redirect('vendor_history', pk=vendor.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid payment. Amount is required.")
        return redirect('vendor_history', pk=self.kwargs['pk'])


class VendorEditPaymentView(UpdateView):
    model = Expense
    fields = ['amount', 'comment']
    pk_url_kwarg = 'payment_pk'

    def get_queryset(self):
        return Expense.objects.filter(expense_type="Vendor Payment")

    def form_valid(self, form):
        expense = form.save()
        # Expense.save() calls vendor.update_vendor() for Vendor Payment type,
        # but we call it explicitly here as well to be safe on edit.
        if expense.vendor:
            expense.vendor.update_vendor()
        messages.success(self.request, f"Payment updated to ₹{expense.amount}.")
        return redirect('vendor_history', pk=self.kwargs['pk'])

    def form_invalid(self, form):
        messages.error(self.request, "Invalid amount.")
        return redirect('vendor_history', pk=self.kwargs['pk'])


class VendorDeletePaymentView(DeleteView):
    model = Expense
    pk_url_kwarg = 'payment_pk'

    def get_queryset(self):
        return Expense.objects.filter(expense_type="Vendor Payment")

    def get_success_url(self):
        return reverse('vendor_history', kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        expense = self.get_object()
        amount = expense.amount
        # Expense.delete() already calls vendor.update_vendor() via the model,
        # so balance recalculates automatically.
        response = super().form_valid(form)
        messages.success(self.request, f"Payment of ₹{amount} deleted.")
        return response
