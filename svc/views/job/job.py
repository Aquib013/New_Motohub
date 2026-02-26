import json
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q, OuterRef, Subquery
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView,
    ListView,
    DeleteView,
    UpdateView,
    DetailView,
)

from django.urls import reverse_lazy, reverse
from weasyprint import HTML

from svc.models import Job, Service, Customer, Vehicle
from svc.forms import JobForm
from svc.models.customer import CUSTOMER_CHOICE


class JobCreateView(CreateView):
    model = Job
    form_class = JobForm
    template_name = "job/job_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer_types'] = dict(CUSTOMER_CHOICE)
        return context

    def form_valid(self, form):
        job = form.save(commit=False)
        job.save()
        messages.success(self.request, "Job Created Successfully.")
        return redirect(reverse('job_detail', kwargs={'pk': job.pk}))

    def form_invalid(self, form):
        # Collect all form errors and add them as messages
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form.fields[field].label}: {error}")
        return super().form_invalid(form)


def search_customers(request):
    query = request.GET.get('query', '')
    customer_type = request.GET.get('type', '')

    customers = Customer.objects.filter(
        Q(customer_name__icontains=query) | Q(customer_mob_no__icontains=query)
    )

    if customer_type:
        customers = customers.filter(customer_type=customer_type)

    customer_list = [
        {'id': c.id, 'name': c.customer_name, 'mobile': c.customer_mob_no, 'customer_type': c.customer_type} for c in
        customers]

    if not customer_list:
        customer_list.append({
            'id': 'new',
            'name': f"Create new customer: {query}",
            'mobile': query if query.isdigit() and len(query) == 10 else '',
            'customer_type': customer_type
        })

    return JsonResponse(list(customer_list), safe=False)


def get_customer_details(request):
    customer_id = request.GET.get('id')
    try:
        customer = Customer.objects.get(id=customer_id)
        return JsonResponse({
            'name': customer.customer_name,
            'mobile': customer.customer_mob_no
        })
    except Customer.DoesNotExist:  # NOQA
        return JsonResponse({'error': 'Customer not found'}, status=404)


@csrf_exempt
def create_customer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            customer = Customer.objects.create(
                customer_name=data['customer_name'],
                customer_mob_no=data['customer_mob_no'],
                customer_type=data['customer_type']
            )
            return JsonResponse({
                'id': customer.id,
                'name': customer.customer_name,
                'mobile': customer.customer_mob_no,
                'customer_type': customer.customer_type
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


class JobListView(ListView):
    model = Job
    template_name = "job/jobs.html"
    context_object_name = "jobs"

    def get_queryset(self):
        selected_date = self.request.GET.get('date')
        if selected_date:
            queryset = Job.objects.filter(job_date=selected_date)
        else:
            queryset = Job.objects.filter(job_date=timezone.now().date())
        return queryset.order_by('job_no')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = context['jobs']
        context['show_completion_time'] = any(job.status == "Completed" for job in jobs)
        context['selected_date'] = self.request.GET.get('date', timezone.now().date().isoformat())
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
        self.object = self.get_object()  # NOQA
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
