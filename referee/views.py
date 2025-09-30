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
        if user is not None and hasattr(user, 'referee_profile'):  # check if referee
            login(request, user)
            return redirect('referee_dashboard')
        else:
            return render(request, "referee_login.html", {"error": "Invalid credentials"})
    return render(request, "referee_login.html")


@login_required(login_url="/referee/login/")
@user_passes_test(is_referee, login_url="/referee/login/")
def referee_dashboard(request):
    referee_profile = request.user.referee_profile
    tournaments = referee_profile.tournaments.all().prefetch_related("matches")  # assumes Tournament has matches

    return render(request, "referee_dashboard.html", {
        "referee": referee_profile,
        "tournaments": tournaments,
    })

@login_required(login_url="/referee/login/")
def refree_matches(request, tournament_id):
    """
    Redirect referee to the organiser matches page for the tournament.
    Only allow if referee is assigned to this tournament.
    """
    # Check if referee is assigned to this tournament
    if not hasattr(request.user, "referee_profile") or \
       not request.user.referee_profile.tournaments.filter(id=tournament_id).exists():
        # Not assigned → block access
        return redirect("/referee/login/")  # or return HttpResponseForbidden()

    # Redirect to organiser view
    return redirect("organisers_matches", tournament_id=tournament_id)

