from django import forms
from svc.models import Service
from svc.models.service import MACHINING_CHOICES, WORKSHOP_CHOICES


class ServiceForm(forms.ModelForm):
    job_hidden = forms.CharField(widget=forms.HiddenInput(), required=True)
    custom_description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control custom-description',
            'style': 'display: none;',
            'placeholder': 'Enter custom service description'
        })
    )

    class Meta:
        model = Service
        fields = ["service_type", "description", "custom_description", "quantity", "unit_service_cost"]

    def __init__(self, *args, **kwargs):
        job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)
        if job:
            self.fields['job_hidden'].initial = job.pk
            self.fields['job'] = forms.CharField(
                initial=job,
                disabled=True,
                required=False,
                widget=forms.TextInput(attrs={'readonly': 'readonly'})
            )
            self.fields['job'].label = 'Job'

        service_type = self.initial.get('service_type', None) or self.data.get('service_type', None)
        if service_type == 'Machining':
            choices = MACHINING_CHOICES
        elif service_type == 'Workshop':
            choices = WORKSHOP_CHOICES
        else:
            choices = [('', '---------')]

        self.fields['description'] = forms.ChoiceField(
            choices=choices,
            widget=forms.Select(attrs={'class': 'form-control service-description'})
        )

    def clean(self):
        cleaned_data = super().clean()
        description = cleaned_data.get('description')
        custom_description = cleaned_data.get('custom_description')

        if description == 'Others' and not custom_description:
            raise forms.ValidationError(
                {'custom_description': 'Please provide a custom service description'}
            )

        return cleaned_data