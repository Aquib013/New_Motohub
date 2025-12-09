import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView, DeleteView

from svc.forms import ServiceForm
from svc.models import Service, Job
from svc.models.service import MACHINING_CHOICES, WORKSHOP_CHOICES, SERVICE_TYPE


class ServiceCreateView(FormView):
    model = Service
    form_class = ServiceForm
    template_name = 'services/service_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['job'] = get_object_or_404(Job, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        job_id = self.kwargs['pk']
        job = get_object_or_404(Job, pk=job_id)
        service = form.save(commit=False)
        service.job = job
        service.save()
        messages.success(self.request, f"Service successfully added to Job #{job.job_no}")

        return redirect('job_detail', pk=job_id)

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
        context['job'] = get_object_or_404(Job, pk=self.kwargs['pk'])
        context['machining_choices'] = json.dumps(MACHINING_CHOICES)
        context['workshop_choices'] = json.dumps(WORKSHOP_CHOICES)
        context['form_media'] = self.form_class().media

        return context


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
