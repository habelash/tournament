from django.contrib import admin
from .models import LeagueAssignment,TournmentMatch
from .utils import reshuffle_leagues
from django.contrib import messages
from .forms import TournmentMatchAdminForm

@admin.register(LeagueAssignment)
class LeagueAssignmentAdmin(admin.ModelAdmin):
    list_display = ('tournament','team', 'league', 'category')
    list_display_links = ('tournament','team', 'league', 'category')
    list_filter = ('tournament','league','category')
    actions = ['refresh_league_assignments']
    
    def refresh_league_assignments(self, request, queryset):
        # Get distinct tournament IDs from the selected assignments
        tournament_ids = queryset.values_list("tournament_id", flat=True).distinct()

        # Run reshuffle for each selected tournament
        for t_id in tournament_ids:
            reshuffle_leagues(tournament_id=t_id, max_per_league=3)  # 👈 change 3 to any default you want

        self.message_user(
            request, 
            f"✅ Leagues reshuffled successfully for {len(tournament_ids)} tournament(s)!",
            messages.SUCCESS
        )

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