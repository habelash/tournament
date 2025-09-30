from django.contrib import admin
from .models import TournamentRegistration
from .models import Payment

# Register your models here.
@admin.register(TournamentRegistration)
class TournmentAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'player_name', 'partner_name', 'phone_number','category','payment_status')
    list_filter = ('tournament','category__category','payment_status')
    search_fields = ('player_name', 'partner_name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'registration', 'order_id', 'txn_amount', 'status', 'created_at')
    list_filter = ('tournament', 'status', 'created_at')
    search_fields = ('tournament', 'order_id', 'txn_id', 'registration__player_name')
