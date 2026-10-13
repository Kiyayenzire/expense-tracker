from datetime import date, timedelta

import re
from unittest.mock import patch
from urllib.parse import unquote

from allauth.account.models import EmailAddress, get_emailconfirmation_model
from allauth.socialaccount.adapter import get_adapter as get_social_adapter
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.contrib.sites.models import Site
from django.test import override_settings
from django.utils import timezone
import pytest
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsLoginAPIContract:
    @override_settings(SITE_ID=1, SOCIALACCOUNT_PROVIDERS={})
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
        response = api_client.get('/api/auth/options/')

        assert response.status_code == status.HTTP_200_OK
        providers = response.json()['providers']
        assert set(providers) == {'google'}
        assert providers['google']['configured'] is True
        assert providers['google']['url'].endswith('/accounts/google/login/')

    @override_settings(
        SITE_ID=1,
        SOCIALACCOUNT_PROVIDERS={
            'google': {
                'APP': {
                    'client_id': 'settings-google-client-id',
                    'secret': 'settings-google-client-secret',
                    'key': '',
                },
            },
        },
    )
    def test_social_auth_options_use_environment_provider_credentials(self, api_client):
        active_site, _ = Site.objects.get_or_create(
            pk=1,
            defaults={'domain': 'localhost', 'name': 'localhost'},
        )
        database_app = SocialApp.objects.create(
            provider='google',
            name='Old database Google app',
            client_id='database-google-client-id',
            secret='database-google-client-secret',
        )
        database_app.sites.add(active_site)

        response = api_client.get('/api/auth/options/')

        assert response.status_code == status.HTTP_200_OK
        providers = response.json()['providers']
        assert providers['google'] == {
            'configured': True,
            'url': 'http://testserver/accounts/google/login/',
        }
        assert set(providers) == {'google'}
        selected_app = get_social_adapter(response.wsgi_request).get_app(
            response.wsgi_request,
            'google',
        )
        assert selected_app.client_id == 'settings-google-client-id'

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
        assert len(mail.outbox) == 1

        resend_response = api_client.post(
            '/api/auth/registration/resend-email/',
            {'email': 'pending@example.com'},
            format='json',
        )
        assert resend_response.status_code == status.HTTP_200_OK
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
        assert login_response.json()['user']['email_verified'] is True

    def test_existing_active_account_can_login_with_unverified_email(self, api_client, test_user):
        EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            primary=True,
            verified=False,
        )

        response = api_client.post(
            '/api/auth/login/',
            {'username': test_user.username, 'password': 'testpass123'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()['user']['email_verified'] is False
        assert response.json()['user']['email_update_required'] is True

    def test_deactivated_email_change_account_must_contact_support(self, api_client, test_user):
        test_user.email_change_requested_at = timezone.now() - timedelta(days=32)
        test_user.email_change_deactivated_at = timezone.now()
        test_user.is_active = False
        test_user.save(update_fields=[
            'email_change_requested_at',
            'email_change_deactivated_at',
            'is_active',
        ])

        with patch('django.core.handlers.base.log_response'):
            response = api_client.post(
                '/api/auth/login/',
                {'username': test_user.username, 'password': 'testpass123'},
                format='json',
            )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'contact support' in response.json()['detail'].lower()

    def test_support_verified_deactivated_account_can_sign_in_before_daily_task(
        self,
        api_client,
        test_user,
    ):
        test_user.email_change_requested_at = timezone.now() - timedelta(days=40)
        test_user.email_change_deactivated_at = timezone.now() - timedelta(days=9)
        test_user.email_change_original_email = test_user.email
        test_user.is_active = False
        test_user.save(update_fields=[
            'email_change_requested_at',
            'email_change_deactivated_at',
            'email_change_original_email',
            'is_active',
        ])
        EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            primary=True,
            verified=True,
        )

        response = api_client.post(
            '/api/auth/login/',
            {'username': test_user.username, 'password': 'testpass123'},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        test_user.refresh_from_db()
        assert test_user.is_active is True
        assert test_user.email_change_requested_at is None
        assert test_user.email_change_deactivated_at is None

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='http://localhost:5174',
    )
    def test_verification_send_failure_is_logged_and_returned_to_authenticated_user(self, authenticated_client, caplog):
        with patch('accounts.tasks.send_mail', side_effect=OSError('SMTP unavailable')):
            with patch('django.core.handlers.base.log_response'):
                response = authenticated_client.post(
                    '/api/auth/registration/resend-email/',
                    format='json',
                )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert 'could not send' in response.json()['detail'].lower()
        assert 'Failed to resend verification email' in caplog.text
        assert 'SMTP unavailable' in caplog.text

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='http://localhost:5174',
    )
    def test_active_unverified_account_can_resend_verification(self, authenticated_client, test_user):
        anonymous_client = APIClient()
        public_response = anonymous_client.post(
            '/api/auth/registration/resend-email/',
            {'email': test_user.email},
            format='json',
        )
        assert public_response.status_code == status.HTTP_200_OK
        assert not EmailAddress.objects.filter(user=test_user).exists()

        response = authenticated_client.post(
            '/api/auth/registration/resend-email/',
            format='json',
        )

        address = EmailAddress.objects.get(user=test_user)
        assert response.status_code == status.HTTP_200_OK
        assert address.verified is False
        assert len(mail.outbox) == 1

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
        assert data['email_verified'] is False
        assert data['email_update_required'] is True
        assert data['email_change_days_remaining'] == 31

    def test_profile_patch_updates_fields(self, authenticated_client, test_user):
        payload = {'first_name': 'Jane', 'last_name': 'Doe', 'phone_number': '0700000000'}
        response = authenticated_client.patch('/api/auth/profile/', payload, format='multipart')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['first_name'] == 'Jane'
        assert data['last_name'] == 'Doe'
        assert data['phone_number'] == '0700000000'

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='http://localhost:5174',
    )
    def test_profile_email_change_requires_verification_and_keeps_old_address_until_confirmed(
        self,
        authenticated_client,
        test_user,
    ):
        response = authenticated_client.patch(
            '/api/auth/profile/',
            {'email': 'new-address@example.com'},
            format='multipart',
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['email'] == test_user.email
        assert data['pending_email'] == 'new-address@example.com'
        assert data['email_change_pending'] is True
        assert data['email_update_required'] is True
        assert data['email_change_days_remaining'] == 31
        test_user.refresh_from_db()
        assert test_user.email == 'test@example.com'
        assert test_user.email_change_requested_at is not None
        address = EmailAddress.objects.get(user=test_user, email='new-address@example.com')
        assert address.verified is False
        assert address.primary is False
        assert len(mail.outbox) == 1

        started_at = test_user.email_change_requested_at
        repeat_response = authenticated_client.patch(
            '/api/auth/profile/',
            {'email': 'new-address@example.com', 'first_name': 'Jane'},
            format='multipart',
        )
        assert repeat_response.status_code == status.HTTP_200_OK
        test_user.refresh_from_db()
        assert test_user.email_change_requested_at == started_at
        assert len(mail.outbox) == 1

        verification_match = re.search(r'#/verify-email/([^\s]+)', mail.outbox[-1].body)
        assert verification_match
        confirmation_key = unquote(verification_match.group(1))
        with patch('allauth.account.adapter.DefaultAccountAdapter.add_message'):
            verification_response = authenticated_client.post(
                '/api/auth/registration/verify-email/',
                {'key': confirmation_key},
                format='json',
            )

        assert verification_response.status_code == status.HTTP_200_OK
        test_user.refresh_from_db()
        address.refresh_from_db()
        assert test_user.email == 'new-address@example.com'
        assert test_user.email_change_requested_at is None
        assert address.verified is True
        assert address.primary is True
        assert verification_response.json()['email_update_required'] is False

    def test_profile_email_change_rejects_another_users_address(self, authenticated_client, test_user, db):
        User.objects.create_user(
            username='other-user',
            email='taken@example.com',
            password='testpass123',
        )

        response = authenticated_client.patch(
            '/api/auth/profile/',
            {'email': 'taken@example.com'},
            format='multipart',
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already in use' in str(response.json()).lower()

    def test_verifying_legacy_email_does_not_clear_pending_email_change(
        self,
        authenticated_client,
        test_user,
    ):
        test_user.email_change_requested_at = timezone.now()
        test_user.email_change_original_email = test_user.email
        test_user.save(update_fields=['email_change_requested_at', 'email_change_original_email'])
        current_address = EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            primary=True,
            verified=False,
        )
        pending_address = EmailAddress.objects.create(
            user=test_user,
            email='new-address@example.com',
            primary=False,
            verified=False,
        )
        confirmation = get_emailconfirmation_model().create(current_address)

        with patch('allauth.account.adapter.DefaultAccountAdapter.add_message'):
            response = authenticated_client.post(
                '/api/auth/registration/verify-email/',
                {'key': confirmation.key},
                format='json',
            )

        assert response.status_code == status.HTTP_200_OK
        test_user.refresh_from_db()
        current_address.refresh_from_db()
        pending_address.refresh_from_db()
        assert current_address.verified is True
        assert pending_address.verified is False
        assert test_user.email_change_requested_at is not None
        assert response.json()['pending_email'] == pending_address.email


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
