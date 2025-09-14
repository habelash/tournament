from django.urls import path
from . import views

urlpatterns = [
    path("referee/dashboard/", views.referee_dashboard, name="referee_dashboard"),
]
