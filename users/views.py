from django.shortcuts import render

# Create your views here.
def user_dashboard(request):
    return render(request, 'user_dashboard.html')

def edit_profile(request):
    return render(request, 'user_dashboard.html')

def change_password(request):
    return render(request, 'user_dashboard.html')

def logout(request):
    return render(request, 'user_dashboard.html')