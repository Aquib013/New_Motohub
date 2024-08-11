from decimal import Decimal
from django.db import models
from django.db.models import Sum, Max
from svc.models import BaseModel


class Vendor(BaseModel):
    firm_name = models.CharField()
    vendor_name = models.CharField()
    vendor_contact_no = models.CharField(unique=True)
    vendor_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    last_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_purchase_date = models.DateTimeField(null=True, blank=True)

    def update_vendor(self):
        # Calculate and update vendor_balance based on related PurchaseOrders
        total_po_amount = self.purchase_orders.aggregate(total=Sum('po_amount'))['total'] or Decimal('0.00')  # NOQA
        last_purchase = self.purchase_orders.aggregate(last_date=Max("created_at"))['last_date']  # NOQA
        self.last_purchase_date = last_purchase
        self.vendor_balance = total_po_amount

        self.save()

    def __str__(self):
        return self.firm_name


