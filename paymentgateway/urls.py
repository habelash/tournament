from django.urls import path
from . import views

urlpatterns = [
    path('phonepe/initiate/<int:registration_id>/', views.initiate_phonepe_payment, name='phonepe_initiate'),
    path('phonepe/callback/', views.phonepe_callback, name='phonepe_callback'),
]
