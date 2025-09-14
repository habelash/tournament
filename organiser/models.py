from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# Create your models here.
class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Tournament(models.Model):
    name = models.CharField(max_length=200)
    categories = models.ManyToManyField(
        Category,
        through="TournamentCategory",
        related_name="tournaments"
    )

    def __str__(self):
        return self.name


class TournamentCategory(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="tournament_categories")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="tournament_categories")  
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.category.name}"
    

class Court(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="courts"
    )
    name = models.CharField(max_length=100)   # Example: "Court 1", "Main Court"
    location = models.CharField(max_length=200, blank=True, null=True)  # Optional
    is_active = models.BooleanField(default=True)  # For enabling/disabling courts
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.location} - {self.name}"
