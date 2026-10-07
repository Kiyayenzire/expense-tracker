from datetime import date

import re
from unittest.mock import patch
from urllib.parse import unquote

from allauth.account.models import EmailAddress, get_emailconfirmation_model
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.contrib.sites.models import Site
from django.test import override_settings
import pytest
from rest_framework import status

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsLoginAPIContract:
    @override_settings(SITE_ID=1)
    def test_social_auth_options_only_enable_apps_linked_to_current_site(self, api_client):
        active_site, _ = Site.objects.get_or_create(
            pk=1,
            defaults={'domain': 'localhost', 'name': 'localhost'},
        )
        other_site, _ = Site.objects.get_or_create(
            pk=2,
            defaults={'domain': 'other.example.com', 'name': 'Other site'},
        )
        google_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='google-client-id',
            secret='google-client-secret',
        )
        google_app.sites.add(active_site)
        apple_app = SocialApp.objects.create(
            provider='apple',
            name='Apple',
            client_id='apple-client-id',
            secret='apple-client-secret',
        )
        apple_app.sites.add(other_site)

        response = api_client.get('/api/auth/options/')

        assert response.status_code == status.HTTP_200_OK
        providers = response.json()['providers']
        assert providers['google']['configured'] is True
        assert providers['apple']['configured'] is False
        assert providers['google']['url'].endswith('/accounts/google/login/')

    def test_login_requires_credentials(self, api_client):
        response = api_client.post('/api/auth/login/', {'username': '', 'password': ''})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success_for_registered_user(self, api_client, test_user):
        response = api_client.post('/api/auth/login/', {'username': 'testuser', 'password': 'testpass123'})
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert 'key' in payload
        assert 'user' in payload

    def test_login_fails_for_invalid_password(self, api_client, test_user):
        response = api_client.post('/api/auth/login/', {'username': 'testuser', 'password': 'wrongpass'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'incorrect password' in response.json()['detail'].lower()

    @override_settings(
        ACCOUNT_EMAIL_VERIFICATION='mandatory',
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='http://localhost:5174',
    )
    def test_registration_requires_email_confirmation_before_login(self, api_client):
        with patch('accounts.views.send_registration_verification_email.delay') as queued_registration_email:
            response = api_client.post(
                '/api/auth/registration/',
                {
                    'username': 'pendinguser',
                    'email': 'pending@example.com',
                    'password1': 'StrongPassword1!',
                    'password2': 'StrongPassword1!',
                },
                format='json',
            )

        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
        user = User.objects.get(username='pendinguser')
        assert user.is_active is False
        email_address = EmailAddress.objects.get(user=user)
        assert email_address.verified is False
        queued_registration_email.assert_called_once_with(email_address.pk)
        from accounts.tasks import send_registration_verification_email
        assert send_registration_verification_email.run(email_address.pk) is True
        assert mail.outbox

        with patch('accounts.views.send_registration_verification_email.delay') as queued_email:
            resend_response = api_client.post(
                '/api/auth/registration/resend-email/',
                {'email': 'pending@example.com'},
                format='json',
            )
        queued_email.assert_called_once_with(email_address.pk)
        assert resend_response.status_code == status.HTTP_200_OK
        assert send_registration_verification_email.run(email_address.pk) is True
        assert len(mail.outbox) == 2
        verification_match = re.search(r'#/verify-email/([^\s]+)', mail.outbox[-1].body)
        assert verification_match
        confirmation_key = unquote(verification_match.group(1))
        assert get_emailconfirmation_model().from_key(confirmation_key) is not None

        with patch('django.core.handlers.exception.log_response'):
            pending_login = api_client.post(
                '/api/auth/login/',
                {'username': 'pendinguser', 'password': 'StrongPassword1!'},
                format='json',
            )
        assert pending_login.status_code == status.HTTP_403_FORBIDDEN
        assert 'verify your email' in pending_login.json()['detail'].lower()

        with patch('allauth.account.adapter.DefaultAccountAdapter.add_message'):
            verify_response = api_client.post(
                '/api/auth/registration/verify-email/',
                {'key': confirmation_key},
                format='json',
            )
        assert verify_response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.is_active is True
        assert EmailAddress.objects.get(user=user).verified is True

        login_response = api_client.post(
            '/api/auth/login/',
            {'username': 'pendinguser', 'password': 'StrongPassword1!'},
            format='json',
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_registration_rejects_invalid_email_address(self, api_client):
        response = api_client.post(
            '/api/auth/registration/',
            {
                'username': 'invalid-email-user',
                'email': 'not-an-email',
                'password1': 'StrongPassword1!',
                'password2': 'StrongPassword1!',
            },
            format='json',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.json()
        assert not User.objects.filter(username='invalid-email-user').exists()

    def test_registration_reports_duplicate_email_address(self, api_client):
        payload = {
            'username': 'first-email-user',
            'email': 'same@example.com',
            'password1': 'StrongPassword1!',
            'password2': 'StrongPassword1!',
        }
        with patch('accounts.views.send_registration_verification_email.delay'):
            first_response = api_client.post(
                '/api/auth/registration/',
                payload,
                format='json',
            )
            payload['username'] = 'second-email-user'
            duplicate_response = api_client.post(
                '/api/auth/registration/',
                payload,
                format='json',
            )

        assert first_response.status_code == status.HTTP_201_CREATED
        assert duplicate_response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in duplicate_response.json()
        assert not User.objects.filter(username='second-email-user').exists()

    def test_social_login_exchange_code_is_single_use(self, api_client, test_user):
        cache.set('auth:social-login:one-time-code', test_user.pk, timeout=60)

        first_response = api_client.post(
            '/api/auth/social/exchange/',
            {'code': 'one-time-code'},
            format='json',
        )
        second_response = api_client.post(
            '/api/auth/social/exchange/',
            {'code': 'one-time-code'},
            format='json',
        )

        assert first_response.status_code == status.HTTP_200_OK
        assert first_response.json()['user']['username'] == test_user.username
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsProfileAPIContract:
    def test_profile_requires_auth(self, api_client):
        response = api_client.get('/api/auth/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_returns_authenticated_user(self, authenticated_client, test_user):
        response = authenticated_client.get('/api/auth/profile/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['username'] == 'testuser'

    def test_profile_patch_updates_fields(self, authenticated_client, test_user):
        payload = {'first_name': 'Jane', 'last_name': 'Doe', 'phone_number': '0700000000'}
        response = authenticated_client.patch('/api/auth/profile/', payload, format='multipart')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['first_name'] == 'Jane'
        assert data['last_name'] == 'Doe'
        assert data['phone_number'] == '0700000000'


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsPasswordResetAPIContract:
    def test_password_reset_request_accepts_email(self, api_client):
        response = api_client.post('/api/auth/password/reset/', {'email': 'test@example.com'})
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_confirm_requires_fields(self, api_client):
        response = api_client.post('/api/auth/password/reset/confirm/', {'uid': '', 'token': '', 'new_password': ''})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsDeletionAPIContract:
    def test_account_deletion_requires_password(self, authenticated_client):
        response = authenticated_client.post('/api/auth/delete-account/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_account_deletion_marks_pending_state(self, authenticated_client, test_user):
        response = authenticated_client.post('/api/auth/delete-account/', {'password': 'testpass123'})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['pending_deletion'] is True


@pytest.mark.integration
@pytest.mark.django_db
class TestSocialPasswordSecurityAPIContract:
    def test_social_user_can_set_password_without_losing_provider_link(self, authenticated_client, test_user):
        test_user.set_unusable_password()
        test_user.save(update_fields=['password'])
        EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            verified=True,
            primary=True,
        )
        social_account = SocialAccount.objects.create(
            user=test_user,
            provider='google',
            uid='google-user-id',
            extra_data={},
        )

        response = authenticated_client.post(
            '/api/auth/password/set/',
            {
                'new_password': 'StrongPassword2!',
                'confirm_password': 'StrongPassword2!',
            },
            format='json',
        )

        test_user.refresh_from_db()
        login_response = authenticated_client.post(
            '/api/auth/login/',
            {'username': test_user.username, 'password': 'StrongPassword2!'},
        )
        assert response.status_code == status.HTTP_200_OK
        assert test_user.check_password('StrongPassword2!')
        assert SocialAccount.objects.filter(pk=social_account.pk, user=test_user).exists()
        assert login_response.status_code == status.HTTP_200_OK

    def test_password_setup_requires_verified_email(self, authenticated_client, test_user):
        test_user.set_unusable_password()
        test_user.save(update_fields=['password'])
        EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            verified=False,
            primary=True,
        )

        response = authenticated_client.post(
            '/api/auth/password/set/',
            {
                'new_password': 'StrongPassword2!',
                'confirm_password': 'StrongPassword2!',
            },
            format='json',
        )

        test_user.refresh_from_db()
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not test_user.has_usable_password()

    def test_password_setup_cannot_replace_an_existing_password(self, authenticated_client):
        response = authenticated_client.post(
            '/api/auth/password/set/',
            {
                'new_password': 'AnotherPassword2!',
                'confirm_password': 'AnotherPassword2!',
            },
            format='json',
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_disconnect_requires_correct_password(self, authenticated_client, test_user):
        social_account = SocialAccount.objects.create(
            user=test_user,
            provider='google',
            uid='google-user-id',
            extra_data={},
        )

        response = authenticated_client.post(
            '/api/auth/social/disconnect/',
            {'provider': 'google', 'password': 'wrong-password'},
            format='json',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert SocialAccount.objects.filter(pk=social_account.pk).exists()

    def test_disconnect_allows_verified_password_account(self, authenticated_client, test_user):
        EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            verified=True,
            primary=True,
        )
        social_account = SocialAccount.objects.create(
            user=test_user,
            provider='google',
            uid='google-user-id',
            extra_data={},
        )

        response = authenticated_client.post(
            '/api/auth/social/disconnect/',
            {'provider': 'google', 'password': 'testpass123'},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        assert not SocialAccount.objects.filter(pk=social_account.pk).exists()

    def test_last_provider_cannot_be_disconnected_without_verified_email(self, authenticated_client, test_user):
        social_account = SocialAccount.objects.create(
            user=test_user,
            provider='google',
            uid='google-user-id',
            extra_data={},
        )

        response = authenticated_client.post(
            '/api/auth/social/disconnect/',
            {'provider': 'google', 'password': 'testpass123'},
            format='json',
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert SocialAccount.objects.filter(pk=social_account.pk).exists()
