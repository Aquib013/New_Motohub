from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Case, When, F, DecimalField
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from svc.forms.customer import CustomerForm
from svc.models import Customer, Job


class CustomerListView(ListView):
    model = Customer
    template_name = "customer/customers_list.html"
    context_object_name = "customers"
    ordering = ['-created_at']

    def get_queryset(self):
        customers = super().get_queryset()
        for customer in customers:
            customer.update_dues_and_balance()
        return customers

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = self.get_queryset()
        return context


class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customer/customer_form.html"
    success_url = reverse_lazy("customers")

    def form_valid(self, form):
        customer = form.save(commit=False)
        customer.save()
        messages.success(self.request, "Customer Added successfully.")
        return super().form_valid(form)


class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customer/customer_form.html"
    success_url = reverse_lazy("customers")


class CustomerDeleteView(DeleteView):
    model = Customer
    template_name = "customer/customer_confirm_delete.html"
    success_url = reverse_lazy("customers")


class CustomerJobsView(DetailView):
    model = Customer
    template_name = 'customer/customer_jobs.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object

        # Update dues and balance
        customer.update_dues_and_balance()

        jobs = customer.job_set.filter(status='Completed').order_by("-created_at")
        context.update({
            'jobs': jobs,
            'total_dues': customer.dues,
            'total_balance': customer.balance,
        })
        return context


class CustomerJobDetailView(DetailView):
    model = Job
    template_name = "customer/customer_job_detail.html"
    context_object_name = "job"

    def get_object(self, queryset=None):
        customer_id = self.kwargs.get('customer_pk')
        job_id = self.kwargs.get('job_pk')
        return get_object_or_404(Job, customer_id=customer_id, id=job_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.object.customer
        context['services'] = self.object.service_set.all()
        context['items'] = self.object.jobitem_set.all()
        return context
