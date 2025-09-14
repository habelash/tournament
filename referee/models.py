from django.db import models
from django.contrib.auth.models import User
from organiser.models import Tournament

class RefereeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referee_profile")
    tournaments = models.ManyToManyField(Tournament, related_name="referees")

    def __str__(self):
        return f"Referee: {self.user.username}"