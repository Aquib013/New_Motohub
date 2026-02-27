
from django.contrib import messages
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
        context['mechanic_customers'] = Customer.objects.filter(customer_type='Mechanic').order_by('customer_name')
        context['non_mechanic_customers'] = Customer.objects.filter(customer_type='Non-Mechanic').order_by(
            'customer_name')
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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['opening_balance'].disabled = True
        return form


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

        customer.update_dues_and_balance()

        jobs = list(customer.job_set.filter(status='Completed').order_by("job_date", "job_completion_time"))
        # Calculate running dues
        running_dues = customer.opening_balance
        for job in jobs:
            running_dues += job.job_amount - job.paid_amount
            job.running_dues = max(running_dues, 0)
            job.running_balance = abs(min(running_dues, 0))

        # Reverse for display (newest first)
        jobs.reverse()

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


