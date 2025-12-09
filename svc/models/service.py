from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from svc.models import BaseModel, Job, Vehicle

SERVICE_TYPE = (
    ("Machining", "Machining"),
    ("Workshop", "Workshop")
)

MACHINING_CHOICES = (
    ("Block Boring", "Block Boring"),
    ("Valve Grinding", "Valve Grinding"),
    ("Crank Repairing", "Crank Repairing"),
    ("Head Seat Cutting", "Head Seat Cutting"),
    ("Head Repairing", "Head Repairing"),
    ("Guide Fitting", "Guide Fitting"),
    ("Plug Socket Threading", "Plug Socket Threading"),
    ("Housing Fitting", "Housing Fitting"),
    ("Others", "Others")  # Added Others option
)

WORKSHOP_CHOICES = (
    ("Full Servicing", "Full Servicing"),
    ("Clutch Plate Replacement", "Clutch Plate Replacement"),
    ("Timing Chain Replacement", "Timing Chain Replacement"),
    ("Chain Sprocket Replacement", "Chain Sprocket Replacement"),
    ("Lock Set Replacement", "Lock Set Replacement"),
    ("Front Fork Repairing", "Front Fork Repairing"),
    ("Disc Repairing", "Disc Repairing"),
    ("Front Shocker Repairing", "Front Shocker Repairing"),
    ("Welding", "Welding"),
    ("Washing", "Washing"),
    ("Battery Charging", "Battery Charging"),
    ("Self Repairing", "Self Repairing"),
    ("Half Engine Repairing", "Half Engine Repairing"),
    ("Full Engine Repairing", "Full Engine Repairing"),
    ("Miscellaneous Service Charge", "Miscellaneous Service Charge"),
    ("Others", "Others")  # Added Others option
)


class Service(BaseModel):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    service_type = models.CharField(choices=SERVICE_TYPE)
    description = models.CharField(max_length=255)
    custom_description = models.CharField(max_length=255, blank=True, null=True)  # New field for custom descriptions
    quantity = models.PositiveIntegerField(default=1)
    unit_service_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        super().clean()
        if self.description == "Others" and not self.custom_description:
            raise ValidationError('Custom description is required when selecting Others')

        if self.description != "Others":
            if self.service_type == 'Machining' and self.description not in dict(MACHINING_CHOICES):
                raise ValidationError('Invalid description for Machining service type')
            elif self.service_type == 'Workshop' and self.description not in dict(WORKSHOP_CHOICES):
                raise ValidationError('Invalid description for Workshop service type')

    def get_display_description(self):
        """Returns the appropriate description for display"""
        if self.description == "Others":
            return self.custom_description
        return self.description

    def save(self, *args, **kwargs):
        self.service_cost = self.quantity * self.unit_service_cost
        super().save(*args, **kwargs)

    def __str__(self):
        description = self.get_display_description()
        return f"{self.job_no}- {description}"


@receiver(post_save, sender=Service)
@receiver(post_delete, sender=Service)
def update_total_service_cost(sender, instance, **kwargs):
    job = instance.job
    total_cost = job.service_set.aggregate(total_cost=Sum("service_cost"))["total_cost"] or 0.0
    job.total_service_cost = total_cost
    job.save()