from django.shortcuts import render
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .models import CustomUser, PhoneOTP
from twilio.rest import Client
from django.conf import settings 
from .models import PlayerProfile, PlayerRanking
from organiser.models import Tournament
from django.contrib.auth.decorators import login_required
from users.models import CustomUser


TWILIO_SID = settings.TWILIO_SID
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN
TWILIO_PHONE = settings.TWILIO_PHONE

@login_required
def user_dashboard(request, username):

    user = get_object_or_404(CustomUser, username=username)
    player = get_object_or_404(PlayerProfile, user=user)
    
    # Upcoming match (first scheduled)
    upcoming_match = "Null" #Match.objects.filter(players=player, status='scheduled').order_by('start_time').first()

    # Recent matches (last 6)
    recent_matches = "Null" #Match.objects.filter(players=player).order_by('-start_time')[:6]

    # Get latest ranking for the player (by year)
    ranking = PlayerRanking.objects.filter(player=player).order_by('-year').first()

    if ranking:
        rankings = {
            'singles': {
                'rank': ranking.singles_rank,
                'wins': ranking.singles_wins,
            },
            'doubles': {
                'rank': ranking.doubles_rank,
                'wins': ranking.doubles_wins,
            },
            'mixed': {
                'rank': ranking.mixed_doubles_rank,
                'wins': ranking.mixed_doubles_wins,
            },
            'total_matches': ranking.total_matches,
            'total_wins': ranking.total_wins,
            'win_percentage': ranking.win_percentage,
        }
    else:
        rankings = None

    # Stats per month
    stats = {
        'months': ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
        'month_values': [
            ranking.january if ranking else 0,
            ranking.february if ranking else 0,
            ranking.march if ranking else 0,
            ranking.april if ranking else 0,
            ranking.may if ranking else 0,
            ranking.june if ranking else 0,
            ranking.july if ranking else 0,
            ranking.august if ranking else 0,
            ranking.september if ranking else 0,
            ranking.october if ranking else 0,
            ranking.november if ranking else 0,
            ranking.december if ranking else 0,
        ] if ranking else [0]*12
    }

    # Open tournaments
    open_tournaments = Tournament.objects.filter(is_active=True)[:4]

    # Example achievements (static for now)
    achievements = [
        {'title':'3x Champion','icon_html':'<i class="bi bi-trophy-fill text-yellow-400"></i>'},
        {'title':'MVP 2024','icon_html':'<i class="bi bi-star-fill text-green-500"></i>'}
    ]

    context = {
        'player': player,
        'upcoming_match': upcoming_match,
        'recent_matches': recent_matches,
        'rankings': rankings,
        'stats': stats,
        'open_tournaments': open_tournaments,
        'achievements': achievements,
    }

    return render(request, 'user_dashboard.html', context)




def edit_profile(request):
    return render(request, 'user_dashboard.html')

def change_password(request):
    return render(request, 'user_dashboard.html')

def logout(request):
    return render(request, 'user_dashboard.html')


client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def send_otp(phone_number):
    otp_obj, created = PhoneOTP.objects.get_or_create(phone_number=phone_number)
    otp = otp_obj.generate_otp()
    message = f"Your OTP is {otp}"
    client.messages.create(to=phone_number, from_=TWILIO_PHONE, body=message)
    return otp

def phone_login_request(request):
    if request.method == "POST":
        phone = request.POST.get("phone_number")
        if CustomUser.objects.filter(phone_number=phone).exists():
            send_otp(phone)
            request.session['phone_number'] = phone
            return redirect('verify_otp')
        else:
            messages.error(request, "Phone number not registered")
    return render(request, "users/phone_login.html")

def verify_otp(request):
    if request.method == "POST":
        otp_input = request.POST.get("otp")
        phone = request.session.get('phone_number')
        otp_obj = PhoneOTP.objects.filter(phone_number=phone).first()
        if otp_obj and otp_obj.otp == otp_input and otp_obj.is_valid():
            otp_obj.verified = True
            otp_obj.save()
            user = CustomUser.objects.get(phone_number=phone)
            from django.contrib.auth import login
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid OTP")
    return render(request, "users/verify_otp.html")
