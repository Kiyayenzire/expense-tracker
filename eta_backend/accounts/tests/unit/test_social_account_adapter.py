from types import SimpleNamespace

from allauth.account.models import EmailAddress
from allauth.core.context import request_context
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.internal.flows.email_authentication import wipe_password
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory
import pytest
from unittest.mock import patch

from accounts.adapters import CustomAccountAdapter, CustomSocialAccountAdapter

User = get_user_model()


def make_social_login(email, verified=True):
    provider = SimpleNamespace(id='google', app=None, get_settings=lambda: {})
    return SimpleNamespace(
        email_addresses=[SimpleNamespace(email=email, verified=verified)],
        provider=provider,
    )


@pytest.mark.django_db
class TestCustomSocialAccountAdapter:
    def make_user(self, username, email='person@example.com'):
        return User.objects.create_user(
            username=username,
            email=email,
            password='StrongPassword1!',
        )

    def test_links_verified_provider_email_to_single_verified_local_account(self):
        user = self.make_user('existing-user')
        EmailAddress.objects.create(
            user=user,
            email='PERSON@EXAMPLE.COM',
            verified=True,
            primary=True,
        )
        User.objects.filter(pk=user.pk).update(email=' Person@Example.com ')

        result = CustomSocialAccountAdapter().authenticate_by_email(
            make_social_login(' PERSON@EXAMPLE.COM ')
        )

        user.refresh_from_db()
        address = EmailAddress.objects.get(user=user)
        assert result == (user, 'person@example.com')
        assert user.email == 'person@example.com'
        assert address.email == 'person@example.com'
        assert user.has_usable_password()
        wipe_password(RequestFactory().get('/'), user, 'person@example.com')
        user.refresh_from_db()
        assert user.has_usable_password()

    def test_rejects_unverified_provider_email_without_changing_password(self):
        user = self.make_user('provider-unverified')
        EmailAddress.objects.create(
            user=user,
            email='person@example.com',
            verified=True,
            primary=True,
        )

        with pytest.raises(ImmediateHttpResponse) as error:
            CustomSocialAccountAdapter().authenticate_by_email(
                make_social_login('person@example.com', verified=False)
            )

        user.refresh_from_db()
        assert error.value.response.status_code == 403
        assert user.has_usable_password()

    def test_rejects_unverified_local_email_without_changing_password(self):
        user = self.make_user('local-unverified')
        EmailAddress.objects.create(
            user=user,
            email='person@example.com',
            verified=False,
            primary=True,
        )

        with pytest.raises(ImmediateHttpResponse):
            CustomSocialAccountAdapter().authenticate_by_email(
                make_social_login('person@example.com')
            )

        user.refresh_from_db()
        assert user.has_usable_password()

    def test_rejects_duplicate_local_user_matches(self):
        user = self.make_user('first-duplicate')
        EmailAddress.objects.create(
            user=user,
            email='person@example.com',
            verified=True,
            primary=True,
        )
        self.make_user('second-duplicate')

        with pytest.raises(ImmediateHttpResponse):
            CustomSocialAccountAdapter().authenticate_by_email(
                make_social_login('person@example.com')
            )

    def test_new_verified_provider_email_without_local_match_is_not_blocked(self):
        result = CustomSocialAccountAdapter().authenticate_by_email(
            make_social_login('new-person@example.com')
        )

        assert result is None

    def test_allauth_lookup_uses_safe_adapter_to_find_existing_verified_user(self):
        user = self.make_user('allauth-linked-user')
        EmailAddress.objects.create(
            user=user,
            email='person@example.com',
            verified=True,
            primary=True,
        )
        social_login = SocialLogin(
            account=SocialAccount(provider='google', uid='google-user-id'),
            email_addresses=[EmailAddress(email=' PERSON@EXAMPLE.COM ', verified=True)],
            provider=SimpleNamespace(id='google', app=None, get_settings=lambda: {}),
        )

        social_login.lookup()

        assert social_login.user == user
        assert social_login._did_authenticate_by_email == 'person@example.com'
        assert user.has_usable_password()

    def test_allauth_accept_login_links_provider_without_wiping_password(self):
        user = self.make_user('allauth-auto-connect')
        EmailAddress.objects.create(
            user=user,
            email='person@example.com',
            verified=True,
            primary=True,
        )
        social_login = SocialLogin(
            account=SocialAccount(provider='google', uid='google-connect-id'),
            email_addresses=[EmailAddress(email='person@example.com', verified=True)],
            provider=SimpleNamespace(id='google', app=None, get_settings=lambda: {}),
        )
        social_login.lookup()
        social_login.account._provider = SimpleNamespace(name='Google')
        request = RequestFactory().get('/accounts/google/login/callback/')

        with request_context(request), patch.object(CustomSocialAccountAdapter, 'send_notification_mail'):
            social_login._accept_login(request)

        user.refresh_from_db()
        assert SocialAccount.objects.filter(
            user=user,
            provider='google',
            uid='google-connect-id',
        ).exists()
        assert user.has_usable_password()

    def test_provider_claim_is_not_overridden_by_social_app_configuration(self):
        adapter = CustomSocialAccountAdapter()
        provider = SimpleNamespace(id='google')

        assert adapter.is_email_verified(provider, 'person@example.com') is False

    def test_social_signup_normalizes_user_and_email_address(self):
        social_email = EmailAddress(email=' Person@Example.COM ', verified=True)
        social_login = SimpleNamespace(
            user=User(),
            email_addresses=[social_email],
        )

        user = CustomSocialAccountAdapter().populate_user(
            None,
            social_login,
            {'username': 'social-user', 'email': ' Person@Example.COM '},
        )

        assert user.email == 'person@example.com'
        assert social_email.email == 'person@example.com'

    def test_allauth_disconnect_hook_requires_a_local_password(self):
        user = self.make_user('passwordless-disconnect')
        user.set_unusable_password()
        account = SocialAccount(user=user, provider='google', uid='google-user-id')

        with pytest.raises(ValidationError, match='no password'):
            CustomSocialAccountAdapter().validate_disconnect(account, [account])

    def test_email_values_are_normalized(self):
        user = self.make_user('normalized-user', '  Person@Example.COM  ')

        assert user.email == 'person@example.com'
        assert CustomAccountAdapter().clean_email(' Person@Example.COM ') == 'person@example.com'
