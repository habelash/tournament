from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .models import PlayerProfile, PlayerRanking


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'phone_number', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'phone_number', 'username')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'phone_number', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'country', 'age', 'gender', 'wta_rank')
    search_fields = ('full_name', 'country')

@admin.register(PlayerRanking)
class PlayerRankingAdmin(admin.ModelAdmin):
    list_display = ('player', 'year', 'singles_rank', 'total_wins', 'win_percentage')
    list_filter = ('year',)
