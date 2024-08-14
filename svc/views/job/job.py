from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import (
    CreateView,
    ListView,
    DeleteView,
    UpdateView,
    DetailView,
)

from django.urls import reverse_lazy
from weasyprint import HTML

from svc.models import Job, Service, Customer
from svc.forms import JobForm
from svc.models.customer import CUSTOMER_CHOICE


class JobCreateView(CreateView):
    model = Job
    form_class = JobForm
    template_name = "job/job_form.html"
    success_url = reverse_lazy("jobs")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer_types'] = dict(CUSTOMER_CHOICE)
        return context

    def form_valid(self, form):
        job = form.save(commit=False)
        job.save()
        messages.success(self.request, "Job Created Successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Collect all form errors and add them as messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form.fields[field].label}: {error}")
        return super().form_invalid(form)


def get_customers(request):
    customer_type = request.GET.get('type')
    customers = Customer.objects.filter(customer_type=customer_type).values('id', 'customer_name', 'place')
    customer_list = [{'id': c['id'], 'name': f"{c['customer_name']} - {c['place']}"} for c in customers]
    return JsonResponse(list(customer_list), safe=False)


class JobListView(ListView):
    model = Job
    template_name = "job/jobs.html"
    context_object_name = "jobs"
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = context['jobs']
        context['show_completion_time'] = any(job.status == "Completed" for job in jobs)
        return context


class JobDetailView(DetailView):
    model = Job
    template_name = "job/job_detail.html"
    context_object_name = "job"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['services'] = Service.objects.filter(job=self.get_object())
        context['total_service_cost'] = context['services'].aggregate(total_cost=Sum('service_cost'))['total_cost'] or 0
        return context


class JobUpdateView(UpdateView):
    model = Job
    form_class = JobForm
    template_name = "job/job_form.html"
    success_url = reverse_lazy("jobs")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object.customer:
            form.fields['customer_type'].initial = self.object.customer.customer_type
            form.fields['customer'].queryset = Customer.objects.filter(customer_type=self.object.customer.customer_type)
        return form

    def form_valid(self, form):
        job = form.save(commit=False)
        if job.status == 'Completed':
            job.paid_amount = form.cleaned_data.get('add_payment')
        else:
            job.paid_amount = Decimal(0)
        job.save()
        messages.success(self.request, "Job updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Collect all form errors and add them as messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form.fields[field].label}: {error}")
        return super().form_invalid(form)


class JobDeleteView(DeleteView):
    model = Job
    template_name = "job/job_delete.html"
    success_url = reverse_lazy('jobs')  # Replace with your job list URL name

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, "Job deleted successfully.")
        except ValidationError as e:
            messages.error(request, e.message)
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


def generate_invoice(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    services = Service.objects.filter(job=job)
    total_service_cost = services.aggregate(total_cost=Sum('service_cost'))['total_cost'] or 0
    total_item_cost = job.jobitem_set.aggregate(total_cost=Sum('item_price'))['total_cost'] or 0

    context = {
        'job': job,
        'services': services,
        'total_service_cost': total_service_cost,
        'total_item_cost': total_item_cost,
    }

    html_string = render_to_string('job/job_invoice.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{job.job_no}.pdf"'
    return response
