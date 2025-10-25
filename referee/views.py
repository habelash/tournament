from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .utils import is_referee
from organiser.urls import organisers_matches

def referee_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'refereeprofile'):  # check if referee
            login(request, user)
            return redirect('referee_dashboard')
        else:
            return render(request, "referee_login.html", {"error": "Invalid credentials"})
    return render(request, "referee_login.html")


@login_required(login_url="/referee/login/")
@user_passes_test(is_referee, login_url="/referee/login/")
def referee_dashboard(request):
    # Get the referee profile
    referee_profile = request.user.refereeprofile

    # Get tournaments assigned to this referee
    tournaments = referee_profile.tournaments.all()

    if hasattr(referee_profile.tournaments.model, "matches"):
        tournaments = tournaments.prefetch_related("matches")

    return render(request, "referee_dashboard.html", {
        "referee": referee_profile,
        "tournaments": tournaments,
    })


@login_required(login_url="/referee/login/")
def referee_matches(request, tournament_id):
    """
    Redirect referee to the organiser matches page for the tournament.
    Only allow if referee is assigned to this tournament.
    """
    # Ensure user has a RefereeProfile
    if not hasattr(request.user, "refereeprofile"):
        return HttpResponseForbidden("You are not registered as a referee.")

    referee_profile = request.user.refereeprofile

    # Check if referee is assigned to this tournament
    if not referee_profile.tournaments.filter(id=tournament_id).exists():
        return HttpResponseForbidden("You are not assigned to this tournament.")

    # Redirect to organiser view (adjust the URL name as needed)
    return redirect("organisers_matches", tournament_id=tournament_id)