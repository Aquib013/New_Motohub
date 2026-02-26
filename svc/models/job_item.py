from django.db import models
from django.db.models import F, Sum
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from svc.models import BaseModel, Job, Item


class JobItem(BaseModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    custom_item_name = models.CharField(max_length=255, null=True, blank=True)
    item_quantity = models.PositiveIntegerField()
    item_unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.item_price = self.item_quantity * self.item_unit_price
        super().save(*args, **kwargs)

    @property
    def display_name(self):
        return self.custom_item_name if self.custom_item_name else str(self.item)

    def __str__(self):
        return self.display_name


@receiver(pre_save, sender=JobItem)
def update_item_quantity(sender, instance, **kwargs):
    if not instance.item:
        return  # Skip stock update for miscellaneous items

    if instance.pk:
        previous_item = JobItem.objects.get(pk=instance.pk)
        previous_quantity = previous_item.item_quantity if previous_item.item else 0
    else:
        previous_quantity = 0

    item = instance.item
    quantity_difference = instance.item_quantity - previous_quantity
    item.item_quantity_in_stock = F('item_quantity_in_stock') - quantity_difference
    item.save()


@receiver(post_delete, sender=JobItem)
def restore_item_quantity(sender, instance, **kwargs):
    if instance.item:
        instance.item.item_quantity_in_stock = F('item_quantity_in_stock') + instance.item_quantity
        instance.item.save()


@receiver(post_save, sender=JobItem)
@receiver(post_delete, sender=JobItem)
def update_total_item_cost(sender, instance, **kwargs):
    job = instance.job
    total_item_cost = job.jobitem_set.aggregate(total_cost=Sum("item_price"))["total_cost"] or 0.0
    job.total_item_cost = total_item_cost
    job.save()