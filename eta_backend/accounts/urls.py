"""
Accounts app URL configuration.
"""
from django.urls import path
from .views import (
    custom_login,
    custom_password_reset_request,
    custom_password_reset_confirm,
    set_password,
    disconnect_social_account,
    request_account_deletion,
    profile_details,
    auth_options,
    social_login_complete,
    social_login_exchange,
    register_user,
    resend_registration_verification,
    verify_registration_email,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', custom_login, name='custom_login'),
    path('registration/', register_user, name='register_user'),
    path('registration/resend-email/', resend_registration_verification, name='resend_registration_verification'),
    path('registration/verify-email/', verify_registration_email, name='verify_registration_email'),
    path('options/', auth_options, name='auth_options'),
    path('social/complete/', social_login_complete, name='social_login_complete'),
    path('social/exchange/', social_login_exchange, name='social_login_exchange'),
    path('profile/', profile_details, name='profile_details'),
    path('delete-account/', request_account_deletion, name='delete_account'),
    path('password/reset/', custom_password_reset_request, name='rest_password_reset'),
    path('password/reset/confirm/', custom_password_reset_confirm, name='rest_password_reset_confirm'),
    path('password/set/', set_password, name='set_password'),
    path('social/disconnect/', disconnect_social_account, name='disconnect_social_account'),
]