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
            old_instance = Expense.objects.get(pk=self.pk)
            old_amount = old_instance.amount

        super().save(*args, **kwargs)

        if self.expense_type == "Employee Payment":
            if is_new:
                self.update_employee_dues_advance()
            else:
                self.update_employee_dues_advance_on_edit(old_amount)  # NOQA

        elif self.expense_type == "Vendor Payment" and self.vendor:
            # Full recalculation — handles create, edit, and opening_balance correctly
            self.vendor.update_vendor()  # NOQA

    def update_employee_dues_advance(self):
        employee = self.employee
        emp_salary = employee.emp_salary  # NOQA
        amount = self.amount

        if amount > emp_salary:
            extra_amount = amount - emp_salary  # NOQA
            employee.emp_advance = F('emp_advance') + extra_amount
        else:
            due_amount = emp_salary - amount
            employee.emp_dues = F('emp_dues') + due_amount

        employee.save(update_fields=['emp_dues', 'emp_advance'])  # NOQA
        employee.refresh_from_db(fields=['emp_dues', 'emp_advance'])  # NOQA

        if employee.emp_dues == employee.emp_advance:
            employee.emp_dues = 0
            employee.emp_advance = 0
            employee.save(update_fields=['emp_dues', 'emp_advance'])  # NOQA

    def update_employee_dues_advance_on_edit(self, old_amount):
        employee = self.employee
        emp_salary = employee.emp_salary  # NOQA
        new_amount = self.amount
        difference = new_amount - old_amount  # NOQA

        if difference > 0:
            if new_amount > emp_salary:
                extra_amount = new_amount - max(old_amount, emp_salary)  # NOQA
                employee.emp_advance = F('emp_advance') + extra_amount
                employee.emp_dues = F('emp_dues') - min(employee.emp_dues, difference)
            else:
                employee.emp_advance = F('emp_advance') + difference
        else:
            if old_amount >= emp_salary:
                reduced_advance = min(employee.emp_advance, abs(difference))
                employee.emp_advance = F('emp_advance') - Decimal(reduced_advance)
                remaining_difference = abs(difference) - Decimal(reduced_advance)
                if remaining_difference > 0:
                    employee.emp_dues = F('emp_dues') + remaining_difference
            else:
                employee.emp_dues = F('emp_dues') - difference

        employee.save(update_fields=['emp_dues', 'emp_advance'])  # NOQA
        employee.refresh_from_db(fields=['emp_dues', 'emp_advance'])  # NOQA

        if employee.emp_dues == employee.emp_advance:
            employee.emp_dues = 0
            employee.emp_advance = 0
            employee.save(update_fields=['emp_dues', 'emp_advance'])  # NOQA

    def update_employee_on_deletion(self):
        if self.expense_type == "Employee Payment":
            employee = self.employee
            emp_salary = employee.emp_salary   # NOQA
            amount = self.amount

            if amount > emp_salary:
                extra_amount = amount - emp_salary
                employee.emp_advance = F('emp_advance') - extra_amount
            else:
                due_amount = emp_salary - amount
                employee.emp_dues = F('emp_dues') - due_amount

            employee.save(update_fields=['emp_dues', 'emp_advance'])   # NOQA
            employee.refresh_from_db(fields=['emp_dues', 'emp_advance'])   # NOQA

            if employee.emp_dues == employee.emp_advance:
                employee.emp_dues = 0
                employee.emp_advance = 0
                employee.save(update_fields=['emp_dues', 'emp_advance'])   # NOQA

            last_payment = Expense.objects.filter(
                employee=employee,
                expense_type="Employee Payment"
            ).exclude(pk=self.pk).order_by('-created_at').first()

            if last_payment:
                employee.emp_last_payment = last_payment.amount
                employee.emp_last_payment_date = last_payment.created_at
            else:
                employee.emp_last_payment = Decimal('0.00')
                employee.emp_last_payment_date = None

            employee.save(update_fields=['emp_last_payment', 'emp_last_payment_date'])  # NOQA

    def delete(self, *args, **kwargs):
        vendor = self.vendor
        self.update_employee_on_deletion()
        super().delete(*args, **kwargs)

        # Recalculate vendor balance after deletion
        if self.expense_type == "Vendor Payment" and vendor:
            vendor.update_vendor()   # NOQA