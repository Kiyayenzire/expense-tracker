# accounts/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.app_settings import EmailVerificationMethod
from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden


def normalize_email(email):
    return (email or '').strip().lower()

class CustomAccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        return normalize_email(super().clean_email(email))

    def pre_login(
        self,
        request,
        user,
        *,
        email_verification,
        signal_kwargs,
        email,
        signup,
        redirect_url,
    ):
        if (
            signup
            and not user.is_active
            and email_verification == EmailVerificationMethod.MANDATORY
        ):
            return None
        return super().pre_login(
            request,
            user,
            email_verification=email_verification,
            signal_kwargs=signal_kwargs,
            email=email,
            signup=signup,
            redirect_url=redirect_url,
        )

    def get_email_confirmation_url(self, request, emailconfirmation):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5174')
        return f"{frontend_url}/#/verify-email/{emailconfirmation.key}"

    def confirm_email(self, request, email_address):
        confirmed = super().confirm_email(request, email_address)
        if confirmed and not email_address.user.is_active:
            email_address.user.is_active = True
            email_address.user.save(update_fields=['is_active'])
        return confirmed


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        normalized_data = dict(data)
        if 'email' in normalized_data:
            normalized_data['email'] = normalize_email(normalized_data['email'])
        user = super().populate_user(request, sociallogin, normalized_data)
        for email_address in sociallogin.email_addresses:
            email_address.email = normalize_email(email_address.email)
        return user

    def is_email_verified(self, provider, email):
        if getattr(provider, 'id', None) in {'google', 'apple'}:
            return False
        return super().is_email_verified(provider, email)

    def can_authenticate_by_email(self, sociallogin, email):
        if getattr(sociallogin.provider, 'id', None) not in {'google', 'apple'}:
            return False
        return super().can_authenticate_by_email(sociallogin, email)

    def authenticate_by_email(self, sociallogin):
        User = get_user_model()

        for provider_email in sociallogin.email_addresses:
            email = normalize_email(provider_email.email)
            if not email:
                continue

            email_addresses = list(EmailAddress.objects.filter(email__iexact=email))
            user_ids = set(
                User.objects.filter(email__iexact=email).values_list('pk', flat=True)
            )
            user_ids.update(address.user_id for address in email_addresses)
            if not user_ids:
                continue

            if (
                not provider_email.verified
                or not self.can_authenticate_by_email(sociallogin, email)
            ):
                raise self._unsafe_email_link_response()

            if len(user_ids) != 1 or len(email_addresses) != 1:
                raise self._unsafe_email_link_response()

            user = User.objects.filter(pk=next(iter(user_ids))).first()
            address = email_addresses[0]
            if (
                user is None
                or not user.is_active
                or address.user_id != user.pk
                or not address.verified
            ):
                raise self._unsafe_email_link_response()

            if address.email != email:
                address.email = email
                address.save(update_fields=['email'])

            if user.email and normalize_email(user.email) == email and user.email != email:
                user.email = email
                user.save(update_fields=['email'])

            return user, email

        return None

    def validate_disconnect(self, account, accounts):
        if not account.user.has_usable_password():
            raise ValidationError(self.error_messages['no_password'])
        return super().validate_disconnect(account, accounts)

    @staticmethod
    def _unsafe_email_link_response():
        return ImmediateHttpResponse(HttpResponseForbidden(
            'This account could not be linked safely. Sign in with your existing method and contact support to connect the provider.'
        ))