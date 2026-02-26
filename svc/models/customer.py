from django.db import models
from django.db.models import Sum, Case, When, F, DecimalField
from decimal import Decimal

from svc.models import BaseModel

CUSTOMER_CHOICE = [
    ("Mechanic", "Mechanic"),
    ("Non-Mechanic", "Non-Mechanic")
]


class Customer(BaseModel):
    customer_name = models.CharField()
    customer_mob_no = models.CharField(max_length=10, unique=True)
    customer_type = models.CharField(choices=CUSTOMER_CHOICE)
    dues = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                          help_text="Previous dues before using MotoHub")
    balance = models.FloatField(default=0, null=True, blank=True)
    last_billed_date = models.DateField(null=True, blank=True)
    last_billed_amount = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.customer_name}"

    def update_dues_and_balance(self):
        jobs = self.job_set.filter(status='Completed')  # NOQA

        job_calculations = jobs.aggregate(
            total_dues=Sum(Case(
                When(job_amount__gt=F('paid_amount'), then=F('job_amount') - F('paid_amount')),
                default=0,
                output_field=DecimalField()
            )),
            total_balance=Sum(Case(
                When(paid_amount__gt=F('job_amount'), then=F('paid_amount') - F('job_amount')),
                default=0,
                output_field=DecimalField()
            ))
        )

        total_dues = (job_calculations['total_dues'] or Decimal('0.00')) + self.opening_balance
        total_balance = job_calculations['total_balance'] or Decimal('0.00')

        # Offset dues against balance
        net = total_dues - total_balance
        if net > 0:
            total_dues = net
            total_balance = Decimal('0')
        elif net < 0:
            total_dues = Decimal('0')
            total_balance = abs(net)
        else:
            total_dues = Decimal('0')
            total_balance = Decimal('0')

        self.dues = total_dues
        self.balance = total_balance
        self.save()
