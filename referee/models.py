from django.db import models
from django.conf import settings
from organiser.models import Tournament
from users.models import CustomUser

class RefereeProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    tournaments = models.ManyToManyField(Tournament, related_name="referees")

    def __str__(self):
        return f"Referee: {self.user.username}"