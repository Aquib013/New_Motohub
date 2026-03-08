from django.utils.timezone import localdate
from django_select2 import forms as s2forms

from svc.models import JobItem, Item, Vehicle
from svc.models.customer import CUSTOMER_CHOICE

from django import forms
from svc.models import Job, Customer


class JobForm(forms.ModelForm):
    customer_type = forms.ChoiceField(choices=[('', 'Select customer type')] + CUSTOMER_CHOICE,
                                      required=False, label="Customer Type")
    job_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=localdate
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        widget=s2forms.Select2Widget
    )
    add_payment = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Add Payment")
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False, widget=forms.HiddenInput())

    class Meta:
        model = Job
        fields = ["job_date", "customer_type", "customer", "vehicle", "license_plate", "total_run", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['customer_type'].widget.attrs.update({'class': 'form-control'})

        self.fields['customer'] = forms.ModelChoiceField(
            queryset=Customer.objects.none(),
            widget=forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            empty_label="Select a customer"
        )

        self.fields['license_plate'].widget.attrs.update({
            'placeholder': 'Enter vehicle number',
        })

        self.fields['total_run'].widget.attrs.update({
            'placeholder': 'Enter vehicle Distance Travelled',
        })

        self.fields['add_payment'].widget.attrs.update({'class': 'payment-field',
                                                        'placeholder': 'Enter the Amount Paid'})

        if 'customer_type' in self.data:
            try:
                customer_type = self.data.get('customer_type')
                self.fields['customer'].queryset = Customer.objects.filter(customer_type=customer_type)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
            # If this is an existing job, set the initial customer_type and customer queryset
        elif self.instance.pk and self.instance.customer:
            self.fields['customer_type'].initial = self.instance.customer.customer_type
            self.fields['customer'].initial = self.instance.customer
            self.fields['customer'].queryset = Customer.objects.filter(
                customer_type=self.instance.customer.customer_type)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        add_payment = cleaned_data.get('add_payment')
        customer_type = cleaned_data.get('customer_type')
        customer = cleaned_data.get('customer')

        if status == 'Completed' and add_payment is None:
            raise forms.ValidationError({
                'add_payment': 'This field is required when the job status is completed.'
            })
        if customer and customer_type:
            if customer.customer_type != customer_type:
                raise forms.ValidationError("Selected customer does not match the chosen customer type.")

        return cleaned_data


class JobItemForm(forms.ModelForm):
    job_hidden = forms.CharField(widget=forms.HiddenInput(), required=False)
    is_custom = forms.BooleanField(
        required=False,
        label="Miscellaneous Item?",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'onchange': 'toggleCustomItem(this)'
        })
    )
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        widget=s2forms.Select2Widget,
        required=False
    )
    custom_item_name = forms.CharField(
        required=False, label="Item Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter item name'})
    )
    discount_percentage = forms.DecimalField(
        max_digits=5, decimal_places=2, required=False, label="Discount %",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount %', 'step': '0.01'})
    )

    class Meta:
        model = JobItem
        fields = ["item", "custom_item_name", "item_quantity", "item_unit_price"]

    def __init__(self, *args, **kwargs):
        job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)

        self.fields['item_unit_price'].required = False
        self.fields['item_unit_price'].widget.attrs.update({
            'placeholder': 'Auto-calculated or enter manually',
        })

        if job:
            self.fields['job_hidden'].initial = job.pk
            self.fields['job'] = forms.CharField(initial=job, disabled=True, required=False)
            self.fields['job'].label = 'Job'

    def clean(self):
        cleaned_data = super().clean()
        is_custom = cleaned_data.get('is_custom')
        item = cleaned_data.get('item')
        custom_item_name = cleaned_data.get('custom_item_name')
        item_quantity = cleaned_data.get('item_quantity')
        item_unit_price = cleaned_data.get('item_unit_price')
        discount_percentage = cleaned_data.get('discount_percentage')

        if is_custom:
            if not custom_item_name:
                self.add_error('custom_item_name', 'Item name is required.')
            if not item_unit_price:
                raise forms.ValidationError("Please enter the unit price for miscellaneous items.")
        else:
            if not item:
                self.add_error('item', 'Please select an item or check Miscellaneous Item.')

            # Auto-calculate unit price from discount
            if item and discount_percentage is not None and not item_unit_price:
                from decimal import Decimal
                import math
                mrp = item.item_MRP
                discount_amount = (mrp * discount_percentage) / Decimal('100')
                raw_price = float(mrp - discount_amount)
                cleaned_data['item_unit_price'] = int(math.ceil(raw_price / 10) * 10)

            item_unit_price = cleaned_data.get('item_unit_price')
            if not item_unit_price:
                raise forms.ValidationError("Please enter either discount percentage or unit price.")

            if item and item_quantity is not None:
                if item_quantity > item.item_quantity_in_stock:
                    raise forms.ValidationError(
                        f"Quantity exceeds available stock. Max available: {item.item_quantity_in_stock}"
                    )

            if item and item_unit_price is not None:
                if item_unit_price < item.cost_price:
                    raise forms.ValidationError(
                        f"Price must be greater than cost price: {item.cost_price}"
                    )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.item_unit_price = self.cleaned_data['item_unit_price']
        if self.cleaned_data.get('is_custom'):
            instance.item = None
            instance.custom_item_name = self.cleaned_data['custom_item_name']
        if commit:
            instance.save()
        return instance