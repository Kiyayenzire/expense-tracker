from datetime import date
import re
from unittest.mock import patch
from urllib.parse import unquote

from allauth.account.models import EmailAddress
from django.core import mail
from django.test import override_settings
import pytest
from rest_framework import status


@pytest.mark.e2e
@pytest.mark.django_db
class TestAccountsUserFlow:
    @override_settings(
        ACCOUNT_EMAIL_VERIFICATION='mandatory',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='http://localhost:5174',
    )
    def test_account_registration_and_profile_flow(self, api_client):
        with patch('accounts.views.send_registration_verification_email.delay'):
            response = api_client.post(
                '/api/auth/registration/',
                {
                    'username': 'newuser',
                    'email': 'newuser@example.com',
                    'password1': 'StrongPassword1!',
                    'password2': 'StrongPassword1!',
                },
                format='json',
            )
        assert response.status_code == status.HTTP_201_CREATED
        new_user = __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.get(username='newuser')
        email_address = EmailAddress.objects.get(user=new_user)
        from accounts.tasks import send_registration_verification_email
        assert send_registration_verification_email.run(email_address.pk) is True
        verification_key = unquote(re.search(r'#/verify-email/([^\s]+)', mail.outbox[-1].body).group(1))
        with patch('allauth.account.adapter.DefaultAccountAdapter.add_message'):
            verify_response = api_client.post('/api/auth/registration/verify-email/', {'key': verification_key}, format='json')
        assert verify_response.status_code == status.HTTP_200_OK

        login_response = api_client.post(
            '/api/auth/login/',
            {'username': 'newuser', 'password': 'StrongPassword1!'},
            format='json',
        )
        assert login_response.status_code == status.HTTP_200_OK

        token = login_response.json()['key']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        profile_response = api_client.get('/api/auth/profile/')
        assert profile_response.status_code == status.HTTP_200_OK

        patch_response = api_client.patch(
            '/api/auth/profile/',
            {'first_name': 'New', 'last_name': 'User', 'phone_number': '0701234567'},
            format='multipart',
        )
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.json()['first_name'] == 'New'

    def test_login_reports_username_and_password_failures_exactly(self, api_client, test_user):
        missing_user_response = api_client.post(
            '/api/auth/login/',
            {'username': 'does-not-exist@example.com', 'password': 'WrongPassword123!'},
            format='json',
        )
        assert missing_user_response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'not found' in missing_user_response.json()['detail'].lower()

        wrong_password_response = api_client.post(
            '/api/auth/login/',
            {'username': 'test@example.com', 'password': 'WrongPassword123!'},
            format='json',
        )
        assert wrong_password_response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'incorrect password' in wrong_password_response.json()['detail'].lower()

    def test_password_reset_flow_informs_existing_email(self, api_client, test_user):
        response = api_client.post('/api/auth/password/reset/', {'email': 'test@example.com'})
        assert response.status_code == status.HTTP_200_OK
        assert 'already exists' in response.json()['detail'].lower()
        assert 'reset password' in response.json()['detail'].lower()

    def test_delete_account_flow(self, authenticated_client, test_user):
        response = authenticated_client.post('/api/auth/delete-account/', {'password': 'testpass123'})
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload['pending_deletion'] is True
