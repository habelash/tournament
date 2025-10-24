from django.contrib.auth.models import AbstractUser
from django.db import models
import random
from django.utils import timezone
from django.conf import settings

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)

    def __str__(self):
        return self.username or self.phone_number



class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()
        return self.otp

    def is_valid(self):
        # valid for 5 minutes
        return (timezone.now() - self.created_at).seconds < 300
    

class PlayerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    full_name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True, null=True)
    profile_image = models.ImageField(upload_to='player_images/', blank=True, null=True)
    age = models.PositiveIntegerField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ], blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)
    twitter_link = models.URLField(blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)

    # Optional: store global identifiers or ranks
    wta_rank = models.IntegerField(blank=True, null=True)
    bta_rank = models.IntegerField(blank=True, null=True)  # if badminton tournament

    def __str__(self):
        return self.full_name or self.user.username


class PlayerRanking(models.Model):
    player = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name='rankings'
    )
    year = models.PositiveIntegerField(default=2025)
    singles_rank = models.PositiveIntegerField(blank=True, null=True)
    doubles_rank = models.PositiveIntegerField(blank=True, null=True)
    mixed_doubles_rank = models.PositiveIntegerField(blank=True, null=True)

    singles_wins = models.PositiveIntegerField(default=0)
    doubles_wins = models.PositiveIntegerField(default=0)
    mixed_doubles_wins = models.PositiveIntegerField(default=0)

    total_matches = models.PositiveIntegerField(default=0)
    total_wins = models.PositiveIntegerField(default=0)
    win_percentage = models.FloatField(default=0.0)

    # Monthly stats (optional)
    january = models.PositiveIntegerField(default=0)
    february = models.PositiveIntegerField(default=0)
    march = models.PositiveIntegerField(default=0)
    april = models.PositiveIntegerField(default=0)
    may = models.PositiveIntegerField(default=0)
    june = models.PositiveIntegerField(default=0)
    july = models.PositiveIntegerField(default=0)
    august = models.PositiveIntegerField(default=0)
    september = models.PositiveIntegerField(default=0)
    october = models.PositiveIntegerField(default=0)
    november = models.PositiveIntegerField(default=0)
    december = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_win_percentage(self):
        if self.total_matches > 0:
            self.win_percentage = (self.total_wins / self.total_matches) * 100
        else:
            self.win_percentage = 0
        self.save()

    def __str__(self):
        return f"{self.player.full_name} - {self.year}"
