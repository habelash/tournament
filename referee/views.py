from django.shortcuts import render
from django.http import HttpResponseForbidden

def referee_dashboard(request):
    # Check if user is a referee
    if not hasattr(request.user, "referee_profile"):
        return HttpResponseForbidden("You are not a referee.")

    # Get all tournaments assigned to this referee
    tournaments = request.user.referee_profile.tournaments.all()

    return render(request, "referee/dashboard.html", {"tournaments": tournaments})
