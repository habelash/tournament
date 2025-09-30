from registration.models import Payment
from registration.models import TournamentRegistration
from .models import LeagueAssignment, TournmentMatch,Tournament
from .models import TournamentCategory
from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import get_object_or_404, render
import pdfkit  # Or use WeasyPrint or xhtml2pdf
from collections import defaultdict
import json
import re

# Create your views here.

def registered_players(request):
    payments = Payment.objects.select_related('registration')  # Efficient join
    context = {
        'payments': payments
    }
    return render(request, "registered_players.html", context)

def all_registrations_view(request):
    registrations = TournamentRegistration.objects.all()
    return render(request, 'players_details.html', {'registrations': registrations})

def download_all_registrations_pdf(request):
    registrations = TournamentRegistration.objects.all()
    template = get_template('players_detailspdf.html')
    html = template.render({'registrations': registrations})

    # Convert HTML to PDF
    pdf = pdfkit.from_string(html, False)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="all_registrations.pdf"'
    return response

def fixture_view(request):
    registrations = TournamentRegistration.objects.all()
    fixtures = defaultdict(list)

    for reg in registrations:
        category = reg.category

        if category == 'singles':
            team = reg.player_name
        elif category in ['beginner_men_doubles', 'intermediate_men_doubles',
                          'intermediate_plus_mens_doubles', 'womens_doubles', 'mixed_doubles']:
            team = f"{reg.player_name} & {reg.partner_name}"
        elif category == 'triplets':
            team = f"{reg.player_name} & {reg.partner_name} & {reg.partner_2_name}"
        else:
            team = reg.player_name

        fixtures[category].append(team)

    # Prepare fixtures grouped in rounds (simple Round 1 bracket logic)
    bracket_data = {}
    for category, teams in fixtures.items():
        rounds = []
        round1 = []
        # Pair up teams into Round 1 matches
        for i in range(0, len(teams), 2):
            if i + 1 < len(teams):
                match = f"{teams[i]} vs {teams[i+1]}"
            else:
                match = f"{teams[i]} (bye)"
            round1.append(match)
        rounds.append(('Round 1', round1))
        bracket_data[category] = rounds

    return render(request, 'matches.html', {'bracket_data': bracket_data})


def league(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    teams = LeagueAssignment.objects.filter(tournament=tournament).select_related('team').order_by('category', 'league', 'id')  # fallback sort
    return render(request, 'league.html', {'teams': teams})



def matches_view(request):
    matches = TournmentMatch.objects.filter(round='League').order_by('category', 'league', 'created_at')

    # Group matches by category and league
    grouped = {}
    for match in matches:
        grouped.setdefault(match.category, {}).setdefault(match.league, []).append(match)

    return render(request, 'match.html', {'grouped_matches': grouped})


def get_team_display(team):
    return getattr(team, "name", getattr(team, "player_name", str(team)))


def get_knockout_matches_grouped_by_base_round(tournament, category):
    rounds = TournmentMatch.objects.filter(
        tournament=tournament,
        category=category
    ).order_by("game_number")

    grouped = defaultdict(list)
    for match in rounds:
        base_round = re.sub(r'\s*\d+$', '', match.round).strip()
        grouped[base_round].append(match)

    return dict(grouped)


def get_knockout_matches_grouped_by_base_round(tournament):
    rounds = TournmentMatch.objects.filter(
        tournament=tournament,
    ).select_related("category").order_by("game_number")

    grouped = defaultdict(list)
    for match in rounds:
        base_round = re.sub(r'\s*\d+$', '', match.round).strip()
        grouped[base_round].append(match)

    return dict(grouped)



def get_round_index(round_name):
    # Q -> 0, S -> 1, F -> 2
    if round_name.startswith("Q"):
        return 0
    elif round_name.startswith("S"):
        return 1
    elif round_name.startswith("F"):
        return 2
    return 0  # fallback
def knockout_bracket_view(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    selected_category = request.GET.get("category")

    # Get distinct TournamentCategory IDs and names linked to matches
    categories = (
        TournmentMatch.objects.filter(tournament=tournament)
        .values_list("category", "category__category__name")
        .distinct()
    )

    # If no categories exist for this tournament, just render an empty page
    if not categories:
        return render(request, "knockout_bracket.html", {
            "tournament": tournament,
            "categories": [],
            "category": None,
            "league_matches_by_group": {},
            "grouped_matches": {},
            "league_to_knockout_map_json": "{}",
        })

    # If no category selected (GET param missing/invalid), use the first one
    try:
        if not selected_category:
            selected_category = categories[0][0]  # take first category ID
        else:
            selected_category = int(selected_category)
    except (ValueError, TypeError):
        selected_category = categories[0][0]

    # Now fetch TournamentCategory safely
    tournament_category = (
        TournamentCategory.objects.filter(id=selected_category, tournament=tournament).first()
    )
    if not tournament_category:
        tournament_category = TournamentCategory.objects.filter(
            id=categories[0][0], tournament=tournament
        ).first()

    # League matches
    league_matches_qs = TournmentMatch.objects.filter(
        tournament=tournament,
        category=tournament_category,
        round="League",
    )

    league_matches_by_group = defaultdict(list)
    for match in league_matches_qs:
        league_matches_by_group[match.league].append(match)

    # Knockout matches
    knockout_matches = (
        TournmentMatch.objects.filter(
            tournament=tournament,
            category=tournament_category,
        )
        .exclude(round="League")
    )

    grouped = defaultdict(list)
    match_indices_by_grouped = defaultdict(list)

    for match in knockout_matches:
        base_round = re.sub(r"\s*\d+$", "", match.round).strip()
        grouped[base_round].append(match)
        match_indices_by_grouped[base_round].append(match)

    league_to_knockout_map = {}
    for match in knockout_matches:
        base_round = re.sub(r"\s*\d+$", "", match.round).strip()
        round_index = get_round_index(base_round)
        match_index = match_indices_by_grouped[base_round].index(match)

        if getattr(match, "team1_source", None) and match.team1_source.round == "League":
            league_to_knockout_map[str(match.team1_source.id)] = [round_index, match_index, "team1"]

        if getattr(match, "team2_source", None) and match.team2_source.round == "League":
            league_to_knockout_map[str(match.team2_source.id)] = [round_index, match_index, "team2"]

    return render(request, "knockout_bracket.html", {
        "tournament": tournament,
        "categories": categories,
        "category": tournament_category,
        "league_matches_by_group": dict(league_matches_by_group),
        "grouped_matches": dict(grouped),
        "league_to_knockout_map_json": json.dumps(league_to_knockout_map),
    })



