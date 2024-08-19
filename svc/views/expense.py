from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, DeleteView, UpdateView
from svc.models import Expense, Employee
from svc.forms import ExpenseForm


class ExpenseCreateUpdateView(CreateView, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense/expense_form.html'
    success_url = reverse_lazy('expense_list')

    def get_object(self, queryset=None):
        if 'pk' in self.kwargs:
            return get_object_or_404(Expense, pk=self.kwargs['pk'])
        return None

    def get_initial(self):
        initial = super().get_initial()
        expense = self.get_object() if self.kwargs.get('pk') else None

        if expense:
            if expense.expense_type == 'Other':
                initial['specify_other'] = expense.expense_title
            elif expense.expense_type == "Employee Payment":
                initial["employee"] = expense.employee
            elif expense.expense_type == "Vendor Payment":
                initial["vendor"] = expense.vendor

        return initial

    def form_valid(self, form):
        expense = form.save(commit=False)
        if expense.expense_type == 'Employee Payment':
            expense.employee = form.cleaned_data['employee']
            employee = form.cleaned_data['employee']
            if employee:
                expense.created_at = timezone.now()

                employee.emp_last_payment = expense.amount
                employee.emp_last_payment_date = expense.created_at

                employee.save()

        elif expense.expense_type == "Vendor Payment":
            expense.vendor = form.cleaned_data['vendor']
            vendor = form.cleaned_data['vendor']
            if vendor:
                expense.created_at = timezone.now()

                vendor.last_payment_amount = expense.amount
                vendor.last_payment_date = expense.created_at

                vendor.save()

        elif expense.expense_type == "Other":
            expense.expense_title = form.cleaned_data["specify_other"]
        expense.save()
        messages.success(self.request, "Expense Added Successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            if field == '__all__':
                for error in errors:
                    messages.error(self.request, f"Error: {error}")
            else:
                for error in errors:
                    messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)


class ExpenseListView(ListView):
    model = Expense
    template_name = "expense/expense_list.html"
    context_object_name = "expenses"
    ordering = ['-created_at']

    def get_queryset(self):
        # Get the date from the query params or use today's date
        selected_date = self.request.GET.get('date', timezone.now().date())

        # Filter jobs by the selected date
        queryset = Expense.objects.filter(
            Q(created_at__date=selected_date)
        ).order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_date'] = self.request.GET.get('date', timezone.now().date())
        return context


class ExpenseDeleteView(DeleteView):
    model = Expense
    template_name = 'expense/expense_confirm_delete.html'
    success_url = reverse_lazy("expense_list")
