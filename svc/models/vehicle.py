from django.db import models

from .base import BaseModel
from svc.constants.vehicles import VEHICLE_CHOICES


class Vehicle(BaseModel):
    name = models.CharField(unique=True)
    make = models.CharField(choices=VEHICLE_CHOICES)

    def __str__(self):
        return f"{self.make} - {self.name}"
