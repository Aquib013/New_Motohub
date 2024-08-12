from django import forms
from django_select2 import forms as s2forms


from svc.models import Item, Vehicle


class ItemForm(forms.ModelForm):
    item_for_vehicle = forms.ModelChoiceField(
                        queryset=Vehicle.objects.all(),
                        widget=s2forms.Select2Widget
    )

    class Meta:
        model = Item
        fields = ['item_brand', 'item', 'item_size', "item_type", 'item_for_vehicle', 'item_quantity_in_stock',
                  'item_MRP', 'discount_percentage', 'net_price']

    def clean(self):
        cleaned_data = super().clean()
        discount_percentage = cleaned_data.get("discount_percentage")
        net_price = cleaned_data.get("net_price")

        if discount_percentage and net_price:
            raise forms.ValidationError("Please enter any one of 'net price' or 'discount percentage'.")
        elif not discount_percentage and not net_price:
            raise forms.ValidationError("Please enter either 'net price' or 'discount percentage'.")

        return cleaned_data
