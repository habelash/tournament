from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class PhoneOrEmailBackend(ModelBackend):
    """
    Authenticate using either phone number or email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email') or kwargs.get('phone_number')
        try:
            user = User.objects.filter(phone_number=username).first()
            if not user:
                user = User.objects.filter(email=username).first()
            if user and user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
