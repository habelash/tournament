from django.urls import path
from . import views

urlpatterns = [
    path('user', views.user_dashboard, name='user_dashboard'),
    path('edit_profile', views.edit_profile, name='edit_profile'),
    path('change_password', views.change_password, name='change_password'),
    path('logout', views.logout, name='logout'),
]
