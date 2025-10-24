from django.urls import path
from . import views

urlpatterns = [
    path('user/<str:username>/', views.user_dashboard, name='user_dashboard'),
    path('edit_profile', views.edit_profile, name='edit_profile'),
    path('change_password', views.change_password, name='change_password'),
    path('logout', views.logout, name='logout'),
    path('phone-login/', views.phone_login_request, name='phone_login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
]
