from django.shortcuts import render, redirect
from .models import TournamentRegistration
from django.shortcuts import get_object_or_404
from organiser.models import Tournament, TournamentCategory
# Create your views here.

def tournament_register(request, tournament_id):
    # Always fetch tournament once
    tournament = get_object_or_404(Tournament, id=tournament_id)

    if request.method == "POST":
        player_name = request.POST.get("player_name")
        phone_number = request.POST.get("phone_number")
        player_email = request.POST.get("player_email")
        partner_name = request.POST.get("partner1_name")
        partner_phone_number = request.POST.get("partner1_phone")
        partner_email = request.POST.get("partner1_email")
        partner_2_name = request.POST.get("partner2_name")
        partner_2_number = request.POST.get("partner2_phone")
        partner_2_email = request.POST.get("partner2_email")
        category = request.POST.get("category")

        # Make sure the category exists
        category_instance = get_object_or_404(TournamentCategory, pk=category)

        # Save registration
        registration = TournamentRegistration.objects.create(
            tournament=tournament,
            player_name=player_name,
            phone_number=phone_number,
            player_email=player_email,
            partner_name=partner_name,
            partner_phone_number=partner_phone_number,
            partner_email=partner_email,
            partner_2_name=partner_2_name,
            partner_2_number=partner_2_number,
            partner_2_email=partner_2_email,
            category=category_instance,
            payment_status="Pending",
        )

        # Redirect to payment
        return redirect("paymentgateway:phonepe_initiate", registration_id=registration.id)

    # For GET request → load registration page
    categories = tournament.tournament_categories.select_related("category")
    context = {
        "tournament": tournament,
        "categories": categories,
    }
    return render(request, "registration.html", context)
 
def home(request):
    return render(request, "home.html")

def return_policies(request):
    return render(request, 'policies.html')


def contact_us(request):
    return render(request, 'contact_us.html')


def tournament(request):
    active_tournaments = Tournament.objects.filter(is_active=True)
    past_tournaments = Tournament.objects.filter(is_active=False)
    print(past_tournaments)

    return render(request, "tournament.html", {
        "active_tournaments": active_tournaments,
        "past_tournaments": past_tournaments,
    })
