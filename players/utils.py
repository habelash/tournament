# utils.py
from collections import defaultdict
import string
from .models import LeagueAssignment
from registration.models import TournamentRegistration

def reshuffle_leagues(max_per_league=3):
    league_labels = list(string.ascii_uppercase)
    category_teams = defaultdict(list)

    # Group teams by category
    for team in TournamentRegistration.objects.filter(payment_status__iexact='paid'):
        category_teams[team.category].append(team)

    # Assign to leagues
    for category, teams in category_teams.items():
        for i, team in enumerate(teams):
            league_index = i // max_per_league
            league_name = league_labels[league_index]

            LeagueAssignment.objects.update_or_create(
                team=team,
                tournament=team.tournament,
                defaults={
                    'league': league_name,
                    'category': category,
                }
            )

def get_round_name(num_teams_remaining):
    if num_teams_remaining == 2:
        return "Final"
    elif num_teams_remaining == 4:
        return "Semifinal"
    elif num_teams_remaining == 8:
        return "Quarterfinal"
    else:
        return f"Round of {num_teams_remaining}"