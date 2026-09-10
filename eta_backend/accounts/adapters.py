# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        # Point activate_url directly to your React frontend route
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        return f"{frontend_url}/verify-email/{emailconfirmation.key}"