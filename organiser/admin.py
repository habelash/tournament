# admin.py
from django.contrib import admin
from .models import Expense, Tournament, Category,TournamentCategory
from django.utils.html import format_html


# Change admin titles
admin.site.site_header = "Fivepercentclub Admin"
admin.site.site_title = "Fivepercentclub Admin Portal"
admin.site.index_title = "Welcome to the Fivepercentclub Management Admin"

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'date', 'receipt_link']
    readonly_fields = ['receipt_link']

    def receipt_link(self, obj):
        if obj.receipt:
            return format_html("<a href='{}' target='_blank'>View Receipt</a>", obj.receipt.url)
        return "No Receipt"
    receipt_link.allow_tags = True
    receipt_link.short_description = 'Receipt'

    
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(TournamentCategory)
class TournamentCategoryAdmin(admin.ModelAdmin):
    list_display = ("display_name", "tournament", "category", "is_active", "started_at")

    def display_name(self, obj):
        return f"{obj.tournament.name} - {obj.category.name}"
    display_name.short_description = "Name"
