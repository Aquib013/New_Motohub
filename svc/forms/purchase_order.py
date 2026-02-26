from django import forms
from django.utils.timezone import now

from svc.models import PurchaseOrder


class PurchaseOrderForm(forms.ModelForm):
    po_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=now
    )

    class Meta:
        model = PurchaseOrder
        fields = ['vendor', 'po_date']
