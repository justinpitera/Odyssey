from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

class User(AbstractUser):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    region = models.CharField(max_length=100, null=True)
    rank = models.CharField(max_length=100, default='Cadet')
    hours = models.IntegerField(default=0)
    simbrief_id = models.CharField(max_length=100, null=True)

@receiver(pre_save, sender=User)
def update_user_rank(sender, instance, **kwargs):
    if instance.hours < 250:
        instance.rank = 'Cadet'
    elif 250 <= instance.hours < 1000:
        instance.rank = 'Second Officer'
    elif 1000 <= instance.hours < 3000:
        instance.rank = 'First Officer'
    elif 3000 <= instance.hours < 6000:
        instance.rank = 'Senior First Officer'
    elif instance.hours >= 6000:
        instance.rank = 'Captain'
