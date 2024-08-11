from django import forms
from svc.models import Expense, Employee, Vendor
from svc.models.expense import EXPENSE_TYPE


class ExpenseForm(forms.ModelForm):
    specify_other = forms.CharField(required=False)
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False,
                                      empty_label="-- Select Employee --"
                                      )
    vendor = forms.ModelChoiceField(queryset=Vendor.objects.all(), required=False, empty_label="-- Select Vendor --")

    expense_type = forms.ChoiceField(
        choices=[('', '-- Select Expense Type --')] + EXPENSE_TYPE,
        required=True
    )

    class Meta:
        model = Expense
        fields = ['expense_type', 'amount', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expense_type'].widget.attrs.update({'class': 'form-control', 'id': 'expense_type'}),
        self.fields['amount'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Amount'})
        self.fields['comment'].widget.attrs.update({'class': 'form-control'})
        self.fields['specify_other'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Specify Expense'})
        self.fields['employee'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Select Employee'})
        self.fields['vendor'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Select Vendor'})

    def clean(self):
        cleaned_data = super().clean()
        expense_type = cleaned_data.get('expense_type')
        employee = cleaned_data.get('employee')
        vendor = cleaned_data.get('vendor')
        specify_other = cleaned_data.get('specify_other')

        if expense_type == 'Employee Payment' and not employee:
            raise forms.ValidationError("Employee is required for Employee Payment.")
        elif expense_type == 'Vendor Payment' and not vendor:
            raise forms.ValidationError("Vendor is required for Vendor Payment.")
        elif expense_type == 'Other' and not specify_other:
            raise forms.ValidationError("Please specify the other expense type.")

        return cleaned_data
