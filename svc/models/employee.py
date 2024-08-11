from django.db import models

from svc.models import BaseModel


class Employee(BaseModel):
    emp_name = models.CharField()
    emp_contact = models.CharField(max_length=10, unique=True)
    emp_aadhaar = models.CharField(max_length=12, unique=True)
    emp_address = models.TextField()
    emp_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    emp_dues = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    emp_advance = models.FloatField(default=0)
    emp_last_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    emp_last_payment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.emp_name
