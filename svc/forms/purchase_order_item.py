from django import forms
from django_select2 import forms as s2forms

from svc.models import PurchaseOrderItem, Item


class PurchaseOrderItemForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        widget=s2forms.Select2Widget
    )

    class Meta:
        model = PurchaseOrderItem
        fields = ["item", "item_MRP", "quantity", "discount_percentage", "net_price"]

    def clean(self):
        cleaned_data = super().clean()
        discount_percentage = cleaned_data.get("discount_percentage")
        net_price = cleaned_data.get("net_price")

        if discount_percentage and net_price:
            raise forms.ValidationError("Please enter any one of 'net price' or 'discount percentage'.")
        elif not discount_percentage and not net_price:
            raise forms.ValidationError("Please enter either 'net price' or 'discount percentage'.")

        return cleaned_data
