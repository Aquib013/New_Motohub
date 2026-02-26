from datetime import datetime
from decimal import Decimal
from django.db import models
from django.utils.timezone import now

from svc.models import BaseModel, Vendor


class PurchaseOrder(BaseModel):
    po_number = models.CharField(unique=True, editable=False)
    po_date = models.DateField(default=now, help_text="Date of the PO (can be backdated)")
    vendor = models.ForeignKey(Vendor, related_name="purchase_orders", on_delete=models.CASCADE)
    po_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.po_number:
            vendor_initials = ''.join([word[0].upper() for word in self.vendor.firm_name.split()]) # NOQA
            date_str = self.po_date.strftime('%d%m%y')  # NOQA
            counter = PurchaseOrder.objects.filter(po_date=self.po_date).count() + 1
            self.po_number = f"{vendor_initials}{date_str}{counter:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.vendor} - {self.po_date}'

    def calculate_po_amount(self):
        # Calculate total po_amount based on related PurchaseOrderItems
        total_amount = Decimal('0.0')
        items = self.purchase_order_item.all()  # NOQA
        for item in items:
            total_amount += item.total_amount
        return total_amount
