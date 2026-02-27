import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView, DeleteView

from svc.forms import ServiceForm
from svc.models import Service, Job
from svc.models.service import MACHINING_CHOICES, WORKSHOP_CHOICES


class ServiceUpdateView(UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['job'] = self.object.job
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['job_hidden'] = self.object.job.pk
        return initial

    def form_valid(self, form):
        service = form.save(commit=False)
        service.job = self.object.job
        service.save()
        messages.success(self.request, f"Service successfully updated for Job #{service.job.job_no}")
        return redirect('job_detail', pk=service.job.pk)

    def get_success_url(self):
        return reverse_lazy('job_detail', kwargs={'pk': self.object.job.pk})

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            if field == '__all__':
                for error in errors:
                    messages.error(self.request, f"Error: {error}")
            else:
                for error in errors:
                    messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.object.job  # Get the job from the service being edited
        context['machining_choices'] = json.dumps(list(MACHINING_CHOICES))
        context['workshop_choices'] = json.dumps(list(WORKSHOP_CHOICES))
        return context


class ServiceDeleteView(DeleteView):
    model = Service
    template_name = 'services/service_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('job_detail', kwargs={'pk': self.object.job.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.object.job
        return context
@csrf_exempt
def add_service_ajax(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)

    try:
        data = json.loads(request.body)
        job = Job.objects.get(pk=pk)

        service_type = data.get('service_type')
        description = data.get('description')
        custom_description = data.get('custom_description', '')
        quantity = int(data.get('quantity', 1))
        unit_cost = float(data.get('unit_service_cost', 0))

        if not service_type:
            return JsonResponse({'error': 'Service type is required'}, status=400)
        if not description:
            return JsonResponse({'error': 'Description is required'}, status=400)
        if description == 'Others' and not custom_description:
            return JsonResponse({'error': 'Custom description required for Others'}, status=400)
        if unit_cost <= 0:
            return JsonResponse({'error': 'Enter a valid cost'}, status=400)

        service = Service(
            job=job,
            service_type=service_type,
            description=description,
            custom_description=custom_description if description == 'Others' else '',
            quantity=quantity,
            unit_service_cost=unit_cost,
            service_cost=quantity * unit_cost,
        )
        service.save()

        job.refresh_from_db()

        display_desc = service.custom_description if service.description == 'Others' else service.description

        return JsonResponse({
            'success': True,
            'service': {
                'id': service.id,
                'description': display_desc,
                'service_type': service.service_type,
                'quantity': service.quantity,
                'unit_service_cost': str(service.unit_service_cost),
                'service_cost': str(service.service_cost),
            },
            'job_total_service_cost': str(job.total_service_cost),
            'job_amount': str(job.job_amount),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def delete_service_ajax(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    try:
        service = Service.objects.get(pk=pk)
        job = service.job
        service.delete()
        job.refresh_from_db()
        return JsonResponse({
            'success': True,
            'job_total_service_cost': str(job.total_service_cost),
            'job_amount': str(job.job_amount),
        })
    except Service.DoesNotExist:  # NOQA
        return JsonResponse({'error': 'Service not found'}, status=404)