from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.timezone import now

from svc.models import BaseModel, Customer, Vehicle

JOB_STATUS = (
    ("Pending", "Pending"),
    ("Completed", "Completed"),
)


class Job(BaseModel):
    job_no = models.CharField(unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    job_date = models.DateField(default=now, help_text="Date of the job (can be backdated)")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)
    status = models.CharField(choices=JOB_STATUS, null=True, blank=True, default="Pending")
    license_plate = models.CharField(null=True, blank=True)
    total_run = models.PositiveIntegerField(null=True, blank=True)
    job_completion_time = models.DateTimeField(null=True, blank=True)
    total_service_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_item_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    job_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True)

    def __str__(self):
        return f"{self.customer} - {self.job_no}"

    @staticmethod
    def unique_job_no(date=None):
        if date is None:
            date = datetime.now().date()
        date_str = date.strftime("%d%m%Y")
        with transaction.atomic():
            # Filter by job_date, not created_at
            last_job = Job.objects.filter(job_date=date).select_for_update().order_by("-id").first()
            if last_job is None:
                counter = 1
            else:
                try:
                    last_counter = int(last_job.job_no.split("-")[1])
                    counter = last_counter + 1
                except (IndexError, ValueError):
                    counter = 1

            # Check if this job_no already exists (safety check)
            job_no = f"{date_str}-{counter}"
            while Job.objects.filter(job_no=job_no).exists():
                counter += 1
                job_no = f"{date_str}-{counter}"

            return job_no

    def save(self, *args, **kwargs):
        if not self.job_no:
            self.job_no = self.unique_job_no(self.job_date)   # NOQA
        if self.status == 'Completed' and self.job_completion_time is None:
            self.job_completion_time = timezone.now()
        elif self.status != "Completed":
            self.job_completion_time = None
        item_cost = Decimal(self.total_item_cost) if self.total_item_cost else Decimal(0)
        service_cost = Decimal(self.total_service_cost) if self.total_service_cost else Decimal(0)
        self.job_amount = item_cost + service_cost
        super(Job, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status == "Completed" and self.paid_amount != self.job_amount:
            raise ValidationError("The job cannot be deleted as it has associated dues or balance !")
        super().delete(*args, **kwargs)


@receiver(post_save, sender=Job)
def update_customer_on_job_creation(sender, instance, created, **kwargs):
    if instance.status == 'Completed' and instance.customer is not None:
        customer = instance.customer
        latest_job = customer.job_set.filter(
            status='Completed'
        ).order_by('-job_date', '-job_completion_time').first()

        if latest_job:
            customer.last_billed_amount = latest_job.job_amount
            customer.last_billed_date = latest_job.job_date
            customer.save()


@receiver(post_delete, sender=Job)
def update_customer_on_job_deletion(sender, instance, **kwargs):
    if instance.customer is None:
        return  # Exit the function if there's no customer associated with the job

    customer = instance.customer
    previous_job = Job.objects.filter(
        customer=customer,
        status="Completed"
    ).exclude(id=instance.id).order_by('-job_completion_time', '-created_at').first()

    if previous_job:
        customer.last_billed_amount = previous_job.job_amount
        customer.last_billed_date = previous_job.job_date
    else:
        customer.last_billed_amount = None
        customer.last_billed_date = None

    customer.save()
