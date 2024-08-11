from django import forms

from svc.models import Vendor


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ["firm_name", "vendor_name", "vendor_contact_no"]

