from django.urls import path
from . import views

urlpatterns = [
    path('tournaments/<int:tournament_id>/register', views.tournament_register, name='tournament_register'),
    path('return_policies/', views.return_policies, name='return_policies'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('', views.tournament, name='tournament'),
]
