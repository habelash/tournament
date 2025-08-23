# urls.py
from django.urls import path
from .views import expenses, organisers_matches, update_score, start_match,start_tournament_category,tournament

urlpatterns = [
    path('expenses/', expenses, name='expenses'),
    path('organiser/tournament', tournament, name='tournament'),
    path('organiser/<int:tournament_id>/start_tournament_category', start_tournament_category, name='start_tournament_category'),
    path('organiser/<int:tournament_id>/matches', organisers_matches, name='organisers_matches'),
    path('start_match', start_match, name='start_match'),
    path('update_score', update_score, name='update_score'),
]
