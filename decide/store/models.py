from django.db import models
from base.models import BigBigField


class Vote(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    a = BigBigField()
    b = BigBigField()

    voted = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.voting_id, self.voter_id)

# Profile Mock

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sexo = models.CharField(max_length=2, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    lugar = models.CharField(max_length=30, blank=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
