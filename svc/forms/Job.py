from django import forms
from django_select2 import forms as s2forms

from svc.models import Job, JobItem, Customer, Item
from svc.models.customer import CUSTOMER_CHOICE


class JobForm(forms.ModelForm):
    customer_type = forms.ChoiceField(choices=[('', 'Select customer type')] + CUSTOMER_CHOICE,
                                      required=False, label="Customer Type")
    add_payment = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Add Payment")

    class Meta:
        model = Job
        fields = ["customer_type", "customer", "license_plate", "total_run", "status"]

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
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        widget=s2forms.Select2Widget
    )

    class Meta:
        model = JobItem
        fields = ["item", "item_quantity", "item_unit_price"]

    def __init__(self, *args, **kwargs):
        job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)
        if job:
            self.fields['job_hidden'].initial = job.pk  # NOQA
            self.fields['job'] = forms.CharField(initial=job, disabled=True, required=False)
            self.fields['job'].label = 'Job'

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get("item")
        item_quantity = cleaned_data.get("item_quantity")
        item_unit_price = cleaned_data.get("item_unit_price")

        if item and item_quantity is not None:
            if item_quantity > item.item_quantity_in_stock:
                raise forms.ValidationError(f"Quantity exceeds available stock."
                                            f"Max available: {item.item_quantity_in_stock}")

        if item and item_unit_price is not None:
            if item_unit_price < item.cost_price:
                raise forms.ValidationError(f"Price must be greater than cost price: {item.cost_price}")

        return cleaned_data
