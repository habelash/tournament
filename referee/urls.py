from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("referee/dashboard/", views.referee_dashboard, name="referee_dashboard"),
    path("referee/login/", views.referee_login, name="referee_login"),
    path("referee/matches/<int:tournament_id>", views.referee_matches, name="referee_matches"),
]
