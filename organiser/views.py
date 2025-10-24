from django.shortcuts import render, redirect
from collections import defaultdict
from django.contrib.auth.decorators import login_required
from .models import Expense,Tournament, TournamentCategory
from players.models import TournmentMatch, LeagueAssignment,Tournament
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.db.models import Q
from itertools import combinations
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import math
import random
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
import pytz
from django.contrib.auth.decorators import login_required, user_passes_test
from referee.utils import is_referee_for_tournament, is_referee

def expenses(request):
    expenses = Expense.objects.all()
    return render(request, 'expenses.html', {'expenses': expenses})

@login_required(login_url="/referee/login/")
@user_passes_test(is_referee, login_url="/referee/login/")
def organisers_matches(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
       
    if not is_referee_for_tournament(request.user, tournament):
        return redirect("/referee/login/")  # or return HttpResponseForbidden()
    
    matches = TournmentMatch.objects.filter(tournament=tournament).order_by('category', 'league', 'created_at')

    # Group matches by category and league
    grouped = {}
    for match in matches:
        grouped.setdefault(match.category, {}).setdefault(match.league, []).append(match)
    return render(request, "matches.html",  {'grouped_matches': grouped})

@csrf_exempt
def start_match(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        match_id = data.get('match_id')

        try:
            match = TournmentMatch.objects.get(id=match_id)
            match.is_started = True
            match.save()

            # Notify via WebSocket
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "score_updates",
                    {
                        "type": "send_score_update",
                        "data": {
                            "match_id": match.id,
                            "is_started": True
                        }
                    }
                )

            return JsonResponse({'success': True})

        except TournmentMatch.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Match not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def generate_mirrored_knockout_pairs(league_keys):
    """
    Returns knockout pairs:
    - Avoids same-league first-round matchups
    - Avoids BYE vs BYE
    - Adds named BYEs to reach power of 2
    """
    first_place = [f"{k}1" for k in league_keys]
    second_place = [f"{k}2" for k in reversed(league_keys)]
    teams = first_place + second_place

    # Add BYEs to reach power of 2
    total = len(teams)
    if total <= 0:
        next_power = 0   # or 1, depending on your business logic
    else:
        next_power = 2 ** math.ceil(math.log2(total))

    byes_needed = next_power - total
    bye_names = [f"BYE_{i}" for i in range(1, byes_needed + 1)]
    teams.extend(bye_names)

    def same_league(t1, t2):
        if t1.startswith("BYE") or t2.startswith("BYE"):
            return False
        return t1[0] == t2[0]

    def is_bye(x):
        return x.startswith("BYE")

    max_attempts = 10
    for _ in range(max_attempts):
        shuffled = teams[:]
        random.shuffle(shuffled)
        valid = True
        pairs = []

        for i in range(0, len(shuffled), 2):
            a = shuffled[i]
            b = shuffled[i + 1]
            if is_bye(a) and is_bye(b):
                valid = False
                break
            if same_league(a, b):
                valid = False
                break
            pairs.append((a, b))

        if valid:
            return pairs

    # 🔁 Greedy fallback: force valid pairs
    real_teams = [t for t in teams if not is_bye(t)]
    byes = [t for t in teams if is_bye(t)]
    pairs = []

    while real_teams:
        t1 = real_teams.pop()
        partner_found = False

        for i, t2 in enumerate(real_teams):
            if not same_league(t1, t2):
                pairs.append((t1, t2))
                real_teams.pop(i)
                partner_found = True
                break

        if not partner_found:
            if byes:
                pairs.append((t1, byes.pop()))
            else:
                pairs.append((t1, None))

    # Leftover byes can be added as (bye, None)
    for bye in byes:
        pairs.append((bye, None))

    return pairs

def create_knockout_matches_from_pairs(tournament, category, pairs, game_number):
    created = 0
    skipped = 0

    # Step 1: Flatten all team placeholders (e.g., "A1", "B2")
    flat_teams = []
    for p1, p2 in pairs:
        flat_teams.append(p1)
        if p2:
            flat_teams.append(p2)

    # Step 2: Pad to next power of 2 with random byes (None)
    team_count = len(flat_teams)
    
    if team_count < 2:
        next_power = team_count   # 0 or 1 → no bracket needed
    else:
        next_power = 2 ** math.ceil(math.log2(team_count))

    byes_needed = next_power - team_count

    for _ in range(byes_needed):
        flat_teams.append(None)

    random.shuffle(flat_teams)  # randomly assign byes

    # Step 3: Create first round pairs
    current_pairs = [(flat_teams[i], flat_teams[i + 1]) for i in range(0, len(flat_teams), 2)]

    # Step 4: Calculate total number of rounds
    def get_total_rounds(team_count):
        if team_count < 1:
            return 0  # no teams, no rounds
        return math.ceil(math.log2(team_count))

    total_rounds = get_total_rounds(len(flat_teams))
    current_round = total_rounds

    # Step 5: Round naming
    def get_round_label_by_depth(depth_from_final):
        if depth_from_final == 1:
            return "Final"
        elif depth_from_final == 2:
            return "Semi Final"
        elif depth_from_final == 3:
            return "Quarter Final"
        elif depth_from_final == 4:
            return "Pre Qualifiers"
        else:
            return f"Round of {2 ** depth_from_final}"

    # Step 6: Create matches round by round
    while len(current_pairs) > 0:
        match_count = len(current_pairs)

        if match_count == 1 and current_pairs[0][1] is None:
            break

        round_label = get_round_label_by_depth(current_round)
        round_names = []

        for idx, (p1, p2) in enumerate(current_pairs, start=1):
            match_name = f"{round_label} {idx}" if match_count > 1 else round_label
            round_names.append(match_name)

            note = f"{p1} vs {p2}" if p2 else f"{p1} gets a bye"

            existing_match = TournmentMatch.objects.filter(
                tournament=tournament,
                category=category,
                league="KO",
                round=match_name,
                note=note
            ).first()

            if not existing_match:
                TournmentMatch.objects.create(
                    tournament=tournament,
                    category=category,
                    league="KO",
                    round=match_name,
                    team1=None,
                    team2=None,
                    note=note,
                    game_number=game_number
                )
                game_number += 1
                created += 1
            else:
                skipped += 1

        # Step 7: Prepare next round
        next_round = [f"Winner of {r}" for r in round_names]
        current_pairs = [(next_round[i], next_round[i + 1] if i + 1 < len(next_round) else None)
                         for i in range(0, len(next_round), 2)]

        current_round -= 1

    return created, game_number


def match_flow_view(request):
    category_order = [
        "singles",
        "advanced_mens_doubles",
        "intermediate_mens_doubles",
        "intermediate_+_mens_doubles",
        "beginner_doubles",
        "mixed_doubles",
        "triplets",
        "womens_doubles"
    ]

    context = {}

    for category in category_order:
        matches = (
            TournmentMatch.objects
            .filter(category=category)
            .order_by('game_number')
        )
        league_matches = {}
        knockout_matches = {}

        for match in matches:
            if match.round.lower() == "league":
                league_matches.setdefault(match.league, []).append(match)
            else:
                knockout_matches.setdefault(match.round, []).append(match)

        context[category] = {
            "league": league_matches,
            "knockouts": dict(sorted(knockout_matches.items()))
        }

    return render(request, "match_flow.html", {"fixtures": context})




def notify_score_update(match):
    channel_layer = get_channel_layer()
    ...
    async_to_sync(channel_layer.group_send)(
        "score_updates",
        {
            "type": "send_score_update",
            "data": {
                "match_id": match.id,
                "team1_score": match.team1_score,
                "team2_score": match.team2_score,
                "winner": str(match.winner) if match.winner else None,
                "match_type": "league" if match.round == "League" else "knockout",
                "is_complete": match.is_completed,
                "is_started": match.is_started
            }
        }
    )

def get_top_two_teams(category_name, league_name):
    matches = TournmentMatch.objects.filter(
        category=category_name,
        league=league_name,
        round='League',
        is_completed=True
    )

    team_stats = defaultdict(lambda: {'wins': 0, 'points_scored': 0, 'points_conceded': 0})

    for match in matches:
        winner = match.winner
        if not winner:
            if match.team1_score > match.team2_score:
                winner = match.team1
            elif match.team2_score > match.team1_score:
                winner = match.team2
            else:
                continue  # skip ties

        team_stats[match.team1]['points_scored'] += match.team1_score
        team_stats[match.team1]['points_conceded'] += match.team2_score

        team_stats[match.team2]['points_scored'] += match.team2_score
        team_stats[match.team2]['points_conceded'] += match.team1_score

        team_stats[winner]['wins'] += 1

    sorted_teams = sorted(team_stats.items(), key=lambda x: (
        -x[1]['wins'],
        -(x[1]['points_scored'] - x[1]['points_conceded']),
        -x[1]['points_scored']
    ))

    top_two = [team for team, stats in sorted_teams[:2]]
    return top_two


def update_next_round_slot(match):
    """
    After a match is completed, propagate the winner to the next round.
    Also handles automatic win for BYE matches.
    """
    # ✅ Auto-complete BYE matches
    if not match.is_completed and match.note and "gets a bye" in match.note.lower():
        match.team1_score = 21
        match.team2_score = 0
        match.winner = match.team1
        match.is_started = True
        match.is_completed = True
        match.save()
        # Now propagate winner as if it's completed
        update_next_round_slot(match)
        return

    if not match.is_completed or not match.winner:
        return

    round_phrase = f"Winner of {match.round}".strip()
    winner = match.winner

    readable_name = winner.player_name
    if getattr(winner, 'partner_name', None):
        readable_name += f" & {winner.partner_name}"

    next_matches = TournmentMatch.objects.filter(
        tournament=match.tournament,
        category=match.category,
        league="KO",
        note__icontains=round_phrase
    )

    for next_match in next_matches:
        note_before = next_match.note or ""
        note_after = note_before
        changed = False

        if round_phrase in note_before:
            # Assign to team1/team2 based on phrase position
            if next_match.team1 is None and note_before.find(round_phrase) < note_before.find("vs"):
                next_match.team1 = winner
                changed = True
            elif next_match.team2 is None and note_before.find(round_phrase) > note_before.find("vs"):
                next_match.team2 = winner
                changed = True

            # Replace placeholder in note
            note_after = note_before.replace(round_phrase, readable_name)
            if note_after != note_before:
                next_match.note = note_after
                changed = True

        if changed:
            next_match.save()

        # ✅ Recursive step: if both teams are present and one is a BYE again
        if (next_match.team1 and not next_match.team2) or ("gets a bye" in (next_match.note or "").lower()):
            update_next_round_slot(next_match)

@login_required(login_url="/referee/login/")
@user_passes_test(is_referee, login_url="/referee/login/")
@csrf_exempt
def update_score(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            match_id = data.get("match_id")
            team1_score = int(data.get("team1_score"))
            team2_score = int(data.get("team2_score"))

            match = TournmentMatch.objects.get(id=match_id)
            match.team1_score = team1_score
            match.team2_score = team2_score
            match.is_started = True
            score_diff = abs(team1_score - team2_score)
            match.is_completed = (
                (team1_score >= 21 or team2_score >= 21) and
                (score_diff >= 2 or team1_score == 30 or team2_score == 30)
)

            # Automatically determine the winner
            if team1_score > team2_score:
                match.winner = match.team1
            elif team2_score > team1_score:
                match.winner = match.team2
            else:
                match.winner = None  # Draw or still in progress

            match.save()

            # ✅ If this is a League match, check for top teams and update KO placeholders
            if match.round == "League":
                all_league_matches = TournmentMatch.objects.filter(
                    tournament=match.tournament,
                    category=match.category,
                    league=match.league,
                    round="League"
                )

                if all(m.is_completed for m in all_league_matches):
                    top_teams = get_top_two_teams(match.category, match.league)
                    print(top_teams)

                    if len(top_teams) < 2:
                        print(f"❌ Not enough valid teams in league {match.league} to fill knockout slots.")
                        return JsonResponse({"success": True, "message": "Not enough teams to proceed"})

                    league_code = match.league.upper()
                    placeholders = {
                        f"{league_code}1": top_teams[0],
                        f"{league_code}2": top_teams[1]
                    }

                    for placeholder, registration in placeholders.items():
                        try:
                            league_assignment = LeagueAssignment.objects.get(team=registration, category=match.category)
                        except LeagueAssignment.DoesNotExist:
                            print(f"❌ No LeagueAssignment found for {registration}")
                            continue

                        readable_name = registration.player_name
                        if getattr(registration, 'partner_name', None):
                            readable_name += f" & {registration.partner_name}"

                        knockout_matches = TournmentMatch.objects.filter(
                            tournament=match.tournament,
                            category=match.category,
                            league="KO"
                        ).filter(
                            Q(note__icontains=placeholder)
                        )
                        print(knockout_matches)

                        for ko_match in knockout_matches:
                            changed = False
                            note_before = ko_match.note or ""

                            if placeholder in note_before:
                                ko_match.note = note_before.replace(placeholder, readable_name)
                                changed = True

                            if ko_match.team1 is None and placeholder in note_before:
                                ko_match.team1 = registration
                                changed = True
                            elif ko_match.team2 is None and placeholder in note_before:
                                ko_match.team2 = registration
                                changed = True

                            if changed:
                                ko_match.save()
            
            if match.round != "League" or match.round != "Final" : 
                update_next_round_slot(match)

                
            # ✅ In all cases (League or not), trigger the update
            notify_score_update(match)

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method"})

@login_required(login_url="/referee/login/")
@user_passes_test(is_referee, login_url="/referee/login/")
def start_tournament_category(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)

    if request.method == "POST":
        category_id = request.POST.get("category_id")
        if not category_id:
            # handle missing category_id
            return redirect("start_tournament_category", tournament_id=tournament.id)

        # Fetch all league assignments with related objects
        assignments = LeagueAssignment.objects.select_related('team', 'category')
        
        # Group teams by category_id and league
        grouped = defaultdict(lambda: defaultdict(list))
        for la in assignments:
            grouped[la.category.id][la.league].append(la.team)

        created = 0
        skipped = 0
        game_number = 1

        # Get TournamentCategory and category_id
        tc = get_object_or_404(TournamentCategory, id=category_id, tournament=tournament)

        category_id_only = tc.id

        if category_id_only in grouped:
            for league, teams in grouped[category_id_only].items():
                team_list = list({t.id: t for t in teams}.values())

                if len(team_list) < 2:
                    continue  # not enough teams to form a match

                for team1, team2 in combinations(team_list, 2):
                    exists = TournmentMatch.objects.filter(
                        tournament=tournament,
                        category=tc,
                        league=league,
                        round="League"
                    ).filter(
                        team1__in=[team1, team2],
                        team2__in=[team1, team2]
                    ).exists()

                    if not exists:
                        TournmentMatch.objects.create(
                            tournament=tournament,
                            category=tc,
                            league=league,
                            round="League",
                            team1=team1,
                            team2=team2,
                            game_number=game_number
                        )
                        game_number += 1
                        created += 1
                    else:
                        skipped += 1

            # Generate knockout matches
            league_keys = sorted(grouped[category_id_only].keys())
            pairs = generate_mirrored_knockout_pairs(league_keys)
            knockout_created, game_number = create_knockout_matches_from_pairs(
                tournament, tc, pairs, game_number
            )
            created += knockout_created

        # Mark category as active and set started_at with India timezone
        tc.is_active = True
        india_tz = pytz.timezone("Asia/Kolkata")
        tc.started_at = timezone.now().astimezone(india_tz)
        tc.save()

        return redirect("start_tournament_category", tournament_id=tournament.id)

    # GET request: render page
    categories = tournament.tournament_categories.select_related("category")
    context = {
        "tournament": tournament,
        "categories": categories,
    }
    return render(request, "start_tournament.html", context)


def profile(request):
    return render(request,"profile.html")