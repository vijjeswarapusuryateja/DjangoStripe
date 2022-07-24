from django.db import models
from django.contrib.auth.models import AbstractUser
from djstripe.models import Customer, Subscription


class CustomUser(AbstractUser):
  subscription = models.ForeignKey(Subscription, null=True, blank=True,on_delete=models.SET_NULL)
  customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)

