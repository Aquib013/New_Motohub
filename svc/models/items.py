from django.db import models

from svc.models import Vehicle
from svc.models.base import BaseModel

ITEM_CHOICES = (
    ("MACHINING", "MACHINING"),
    ("WORKSHOP", "WORKSHOP"),
)


class Item(BaseModel):
    item_brand = models.CharField(null=True, blank=True)
    item = models.CharField()
    item_size = models.CharField(null=True, blank=True)
    item_name = models.CharField(editable=False)
    item_for_vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    item_type = models.CharField(choices=ITEM_CHOICES)
    item_quantity_in_stock = models.IntegerField(default=0)
    item_MRP = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    net_price = models.IntegerField(null=True, blank=True)
    cost_price = models.IntegerField()

    def save(self, *args, **kwargs):
        self.item_name = f"{self.item_brand}-{self.item}-{self.item_for_vehicle.name}-{self.item_size}"
        if self.discount_percentage is not None:
            self.cost_price = int(self.item_MRP - (self.item_MRP * (self.discount_percentage / 100)))  # NOQA
        elif self.net_price is not None:
            self.cost_price = int(self.net_price)  # NOQA
        else:
            raise ValueError("Please enter either Discount percentage or Net price")
        super().save(*args, **kwargs)

    def is_low_stock(self):
        return self.item_quantity_in_stock < 2

    def __str__(self):
        return self.item_name
