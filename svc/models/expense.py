from decimal import Decimal

from django.db import models
from django.db.models import F

from svc.models import BaseModel, Employee, Vendor

EXPENSE_TYPE = [
    ("Employee Payment", "Employee Payment"),
    ("Vendor Payment", "Vendor Payment"),
    ("Other", "Other")
]


class Expense(BaseModel):
    expense_type = models.CharField(choices=EXPENSE_TYPE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    employee = models.ForeignKey(Employee, related_name="employee_payments",
                                 on_delete=models.SET_NULL, null=True)
    vendor = models.ForeignKey(Vendor, related_name="vendor_payments",
                               on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    expense_title = models.CharField(null=True, blank=True)

    def __str__(self):
        return f"{self.expense_type}-{self.comment}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            # Get the old instance from the database
            old_instance = Expense.objects.get(pk=self.pk)
            old_amount = old_instance.amount

        super().save(*args, **kwargs)  # Save the expense

        if self.expense_type == "Employee Payment":
            if is_new:
                self.update_employee_dues_advance()
            else:
                self.update_employee_dues_advance_on_edit(old_amount)       # NOQA

        elif self.expense_type == "Vendor Payment":
            if is_new:
                self.update_vendor_balance()
            else:
                self.update_vendor_balance_on_edit(old_amount)     # NOQA

    def update_employee_dues_advance(self):
        employee = self.employee
        emp_salary = employee.emp_salary     # NOQA
        amount = self.amount

        if amount > emp_salary:
            extra_amount = amount - emp_salary       # NOQA
            employee.emp_advance = F('emp_advance') + extra_amount
        else:
            due_amount = emp_salary - amount
            employee.emp_dues = F('emp_dues') + due_amount

        employee.save(update_fields=['emp_dues', 'emp_advance'])      # NOQA

        # Fetch updated values from the database
        employee.refresh_from_db(fields=['emp_dues', 'emp_advance'])     # NOQA

        # Settle advance and dues if they are equal
        if employee.emp_dues == employee.emp_advance:
            employee.emp_dues = 0
            employee.emp_advance = 0
            employee.save(update_fields=['emp_dues', 'emp_advance'])     # NOQA

    def update_employee_dues_advance_on_edit(self, old_amount):
        employee = self.employee
        emp_salary = employee.emp_salary    # NOQA
        new_amount = self.amount
        difference = new_amount - old_amount   # NOQA

        if difference > 0:  # Amount increased
            if new_amount > emp_salary:
                extra_amount = new_amount - max(old_amount, emp_salary)     # NOQA
                employee.emp_advance = F('emp_advance') + extra_amount
                employee.emp_dues = F('emp_dues') - min(employee.emp_dues, difference)

            elif new_amount == emp_salary:
                employee.emp_advance = F('emp_advance') + difference

            else:
                employee.emp_dues = F('emp_dues') - difference
        else:  # Amount decreased
            if old_amount >= emp_salary:
                reduced_advance = min(employee.emp_advance, abs(difference))
                employee.emp_advance = F('emp_advance') - Decimal(reduced_advance)
                remaining_difference = abs(difference) - Decimal(reduced_advance)
                if remaining_difference > 0:
                    employee.emp_dues = F('emp_dues') + remaining_difference
            else:
                employee.emp_dues = F('emp_dues') - difference

        employee.save(update_fields=['emp_dues', 'emp_advance'])   # NOQA
        employee.refresh_from_db(fields=['emp_dues', 'emp_advance'])  # NOQA

        # Settle advance and dues if they are equal
        if employee.emp_dues == employee.emp_advance:
            employee.emp_dues = 0
            employee.emp_advance = 0
            employee.save(update_fields=['emp_dues', 'emp_advance'])   # NOQA

    def update_vendor_balance(self):
        vendor = self.vendor
        amount = self.amount

        vendor.vendor_balance = F('vendor_balance') - amount
        vendor.last_payment_date = self.created_at
        vendor.last_payment_amount = amount

        vendor.save(update_fields=['vendor_balance', 'last_payment_date', 'last_payment_amount'])  # NOQA
        vendor.refresh_from_db(fields=['vendor_balance'])    # NOQA

    def update_vendor_balance_on_edit(self, old_amount):
        vendor = self.vendor
        new_amount = self.amount
        difference = new_amount - old_amount          # NOQA

        vendor.vendor_balance = F('vendor_balance') - difference
        vendor.save(update_fields=['vendor_balance'])                # NOQA
        vendor.refresh_from_db(fields=['vendor_balance'])            # NOQA