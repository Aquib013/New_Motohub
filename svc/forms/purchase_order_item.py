# from django import forms
# from django_select2 import forms as s2forms
#
# from svc.models import PurchaseOrderItem, Item
#
#
# class PurchaseOrderItemForm(forms.ModelForm):
#     item = forms.ModelChoiceField(
#         queryset=Item.objects.all(),
#         widget=s2forms.Select2Widget
#     )
#
#     class Meta:
#         model = PurchaseOrderItem
#         fields = ["item", "item_MRP", "quantity", "discount_percentage", "net_price"]
#
#     def clean(self):
#         cleaned_data = super().clean()
#         discount_percentage = cleaned_data.get("discount_percentage")
#         net_price = cleaned_data.get("net_price")
#
#         if discount_percentage and net_price:
#             raise forms.ValidationError("Please enter any one of 'net price' or 'discount percentage'.")
#         elif not discount_percentage and not net_price:
#             raise forms.ValidationError("Please enter either 'net price' or 'discount percentage'.")
#
#         return cleaned_data

from django import forms
from django_select2 import forms as s2forms

from svc.models import PurchaseOrderItem, Item, Vehicle

ITEM_CHOICES = (
    ("MACHINING", "MACHINING"),
    ("WORKSHOP", "WORKSHOP"),
)


class PurchaseOrderItemForm(forms.ModelForm):
    is_new_item = forms.BooleanField(
        required=False,
        label="Item not found? Add New",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'onchange': 'toggleNewItem(this)'
        })
    )

    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        widget=s2forms.Select2Widget,
        required=False
    )

    # New item fields
    new_item_brand = forms.CharField(
        required=False, label="Brand",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand (optional)'})
    )
    new_item = forms.CharField(
        required=False, label="Item",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name'})
    )
    new_item_size = forms.CharField(
        required=False, label="Size",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Size (optional)'})
    )
    new_item_for_vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        required=False, label="Vehicle",
        widget=s2forms.Select2Widget
    )
    new_item_type = forms.ChoiceField(
        choices=[('', '---------')] + list(ITEM_CHOICES),
        required=False, label="Item Type",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PurchaseOrderItem
        fields = ["item", "item_MRP", "quantity", "discount_percentage", "net_price"]

    def clean(self):
        cleaned_data = super().clean()
        is_new = cleaned_data.get('is_new_item')
        discount_percentage = cleaned_data.get("discount_percentage")
        net_price = cleaned_data.get("net_price")

        if discount_percentage and net_price:
            raise forms.ValidationError(
                "Please enter any one of 'net price' or 'discount percentage'."
            )
        elif not discount_percentage and not net_price:
            raise forms.ValidationError(
                "Please enter either 'net price' or 'discount percentage'."
            )

        if is_new:
            for field, label in {'new_item': 'Item name', 'new_item_for_vehicle': 'Vehicle',
                                 'new_item_type': 'Item type'}.items():
                if not cleaned_data.get(field):
                    self.add_error(field, f"{label} is required for new items.")
        else:
            if not cleaned_data.get('item'):
                self.add_error('item', "Please select an item or check 'Add New Item'.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.cleaned_data.get('is_new_item'):
            new_item = Item(
                item_brand=self.cleaned_data.get('new_item_brand') or None,
                item=self.cleaned_data['new_item'],
                item_size=self.cleaned_data.get('new_item_size') or None,
                item_for_vehicle=self.cleaned_data['new_item_for_vehicle'],
                item_type=self.cleaned_data['new_item_type'],
                item_MRP=self.cleaned_data['item_MRP'],
                discount_percentage=self.cleaned_data.get('discount_percentage'),
                net_price=self.cleaned_data.get('net_price'),
                item_quantity_in_stock=0,
            )
            new_item.save()
            instance.item = new_item

        if commit:
            instance.save()
        return instance