from django.db import models
from organiser.models import Tournament, TournamentCategory


class TournamentRegistration(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="registrations"
    )
    player_name = models.CharField(max_length=100)
    partner_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Player's phone number
    partner_phone_number = models.CharField(max_length=15, blank=True, null=True)  # New field

    player_email = models.EmailField(blank=True, null=True)  # New field
    partner_email = models.EmailField(blank=True, null=True)  # New field

    partner_2_name = models.CharField(max_length=100, blank=True, null=True)
    partner_2_number = models.CharField(max_length=15, blank=True, null=True)  # Player's phone number
    partner_2_email = models.EmailField(blank=True, null=True)  # New field

    category = models.ForeignKey( 
        TournamentCategory,
        on_delete=models.CASCADE,
        related_name="registrations"
    )
    phonepay_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default='Pending')  # Payment status

    screenshot = models.ImageField(upload_to='screenshots/', null=True, blank=True)
    referred_by = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.player_name} / {self.partner_name}" if self.partner_name else self.player_name

class Payment(models.Model):
    registration = models.ForeignKey(TournamentRegistration, on_delete=models.CASCADE, related_name='payments')
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    order_id = models.CharField(max_length=100)
    txn_id = models.CharField(max_length=100, blank=True, null=True)
    txn_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    response_data = models.TextField()  # Store full response JSON/text
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration.player_name} - {self.order_id} - {self.status}"