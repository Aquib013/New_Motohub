from decimal import Decimal
from django.db import models
from django.db.models import Sum, Max
from svc.models import BaseModel


class Vendor(BaseModel):
    firm_name = models.CharField()
    vendor_name = models.CharField()
    vendor_contact_no = models.CharField(unique=True)
    vendor_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor_opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                          help_text="Previous dues before using MotoHub")
    last_payment_date = models.DateTimeField(null=True, blank=True)
    last_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_purchase_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.vendor_balance = self.vendor_opening_balance
        super().save(*args, **kwargs)

    def update_vendor(self):
        # Calculate and update vendor_balance based on related PurchaseOrders
        total_po_amount = self.purchase_orders.aggregate(  # NOQA
            total=Sum('po_amount'))['total'] or Decimal('0.00')

        total_payments = self.vendor_payments.aggregate(  # NOQA
            total=Sum('amount'))['total'] or Decimal('0.00')

        last_purchase = self.purchase_orders.aggregate(  # NOQA
            last_date=Max("po_date"))['last_date']

        last_payment = self.vendor_payments.order_by('-created_at').first()  # NOQA

        self.last_purchase_date = last_purchase

        self.vendor_balance = self.vendor_opening_balance + total_po_amount - total_payments  # NOQA

        if last_payment:
            self.last_payment_date = last_payment.created_at
            self.last_payment_amount = last_payment.amount

        self.save()

    def __str__(self):
        return self.firm_name


