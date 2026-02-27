from django import forms

from svc.models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["customer_name", "customer_mob_no", "opening_balance", "customer_type"]

