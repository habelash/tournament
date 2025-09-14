from django.contrib import admin
from .models import RefereeProfile

@admin.register(RefereeProfile)
class RefereeProfileAdmin(admin.ModelAdmin):
    list_display = ("user",)
    filter_horizontal = ("tournaments",)
