from django import forms
from django_select2 import forms as s2forms


from svc.models import Service, Job, Vehicle
from svc.models.service import MACHINING_CHOICES, WORKSHOP_CHOICES


class ServiceForm(forms.ModelForm):
    job_hidden = forms.CharField(widget=forms.HiddenInput(), required=True)
    vehicle = forms.ModelChoiceField(
                        queryset=Vehicle.objects.all(),
                        widget=s2forms.Select2Widget
    )

    class Meta:
        model = Service
        fields = ["service_type", "description", "vehicle", "quantity", "unit_service_cost"]

    def __init__(self, *args, **kwargs):
        job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)
        if job:
            self.fields['job_hidden'].initial = job.pk  # NOQA
            self.fields['job'] = forms.CharField(initial=job, disabled=True, required=False,
                                                 widget=forms.TextInput(attrs={'readonly': 'readonly'}))
            self.fields['job'].label = 'Job'

        service_type = self.initial.get('service_type', None) or self.data.get('service_type', None)
        if service_type == 'Machining':
            choices = MACHINING_CHOICES
        elif service_type == 'Workshop':
            choices = WORKSHOP_CHOICES
        else:
            choices = [('', '---------')]

        self.fields['description'] = forms.ChoiceField(choices=choices)
