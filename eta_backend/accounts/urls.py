"""
Accounts app URL configuration.
"""
from django.urls import path
from .views import (
    custom_login,
    custom_password_reset_request,
    custom_password_reset_confirm,
    request_account_deletion,
    profile_details,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', custom_login, name='custom_login'),
    path('profile/', profile_details, name='profile_details'),
    path('delete-account/', request_account_deletion, name='delete_account'),
    path('password/reset/', custom_password_reset_request, name='rest_password_reset'),
    path('password/reset/confirm/', custom_password_reset_confirm, name='rest_password_reset_confirm'),
]

