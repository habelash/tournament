from django.contrib import admin
from .models import LeagueAssignment,TournmentMatch
from .utils import reshuffle_leagues
from django.contrib import messages
from .forms import TournmentMatchAdminForm

@admin.register(LeagueAssignment)
class LeagueAssignmentAdmin(admin.ModelAdmin):
    list_display = ('tournament','team', 'league', 'category')
    actions = ['refresh_league_assignments']

    def refresh_league_assignments(self, request, queryset):
        reshuffle_leagues()
        self.message_user(request, "✅ Leagues reshuffled successfully!", messages.SUCCESS)

    refresh_league_assignments.short_description = "🔁 Refresh League Assignments"

@admin.register(TournmentMatch)
class TournmentMatchAdmin(admin.ModelAdmin):
    form = TournmentMatchAdminForm
    list_display = (
        'tournament','game_number', 'category', 'league', 'round',
        'team1', 'team2', 'winner', 'is_started', 'is_completed'
    )
    list_display_links = (
        'tournament', 'game_number', 'category', 'league', 'round',
        'team1', 'team2', 'winner', 'is_started', 'is_completed'
    )