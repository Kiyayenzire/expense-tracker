import os
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from accounts.models import User


@pytest.mark.unit
@pytest.mark.django_db
class TestAccountsUserModel:
    def test_create_user(self, test_user):
        assert test_user.username == 'testuser'
        assert test_user.email == 'test@example.com'
        assert test_user.role == 'user'
        assert not test_user.is_admin()

    def test_user_is_admin_check(self, admin_user):
        assert admin_user.is_admin()
        assert admin_user.role == 'admin'

    def test_user_two_factor_enabled(self, db):
        user = User.objects.create_user(
            username='2fa_user',
            email='2fa@example.com',
            password='pass123',
            two_factor_enabled=True,
        )
        assert user.two_factor_enabled is True

    def test_user_profile_picture_field_exists(self, db):
        user = User.objects.create_user(
            username='avatar_user',
            email='avatar@example.com',
            password='pass123',
        )
        assert hasattr(user, 'profile_picture')
        assert not user.profile_picture.name

    def test_user_can_request_account_deletion(self, test_user):
        test_user.request_account_deletion('testpass123')
        assert test_user.account_deletion_requested_at is not None
        assert test_user.is_account_deletion_pending is True

    def test_login_cancels_pending_account_deletion(self, test_user):
        test_user.account_deletion_requested_at = timezone.now() - timedelta(days=2)
        test_user.save(update_fields=['account_deletion_requested_at'])

        test_user.cancel_account_deletion()

        assert test_user.account_deletion_requested_at is None
        assert test_user.is_account_deletion_pending is False

    def test_expired_account_deletions_are_removed(self, test_user):
        test_user.account_deletion_requested_at = timezone.now() - timedelta(days=32)
        test_user.save(update_fields=['account_deletion_requested_at'])

        deleted_count = User.objects.delete_expired_account_deletions()

        assert deleted_count == 1

    def test_email_lifecycle_starts_deadline_for_active_legacy_unverified_accounts(self, test_user):
        now = timezone.now()

        result = User.objects.process_email_change_lifecycle(now=now)

        test_user.refresh_from_db()
        assert result == {
            'started': 1,
            'deactivated': 0,
            'deleted': 0,
            'reverified': 0,
            'reactivated': 0,
        }
        assert test_user.email_change_requested_at == now
        assert test_user.email_change_deadline == now + timedelta(days=31)

    def test_email_lifecycle_deactivates_then_deletes_after_97_days(self, test_user, admin_user):
        from rest_framework.authtoken.models import Token

        now = timezone.now()
        test_user.email_change_requested_at = now - timedelta(days=32)
        test_user.save(update_fields=['email_change_requested_at'])
        superuser = User.objects.create_superuser(
            username='lifecycle_superuser',
            email='lifecycle-superuser@example.com',
            password='StrongPass123!',
        )
        superuser.email_change_requested_at = now - timedelta(days=200)
        superuser.email_change_deactivated_at = now - timedelta(days=98)
        superuser.is_active = False
        superuser.save(update_fields=[
            'email_change_requested_at',
            'email_change_deactivated_at',
            'is_active',
        ])
        token = Token.objects.create(user=test_user)
        admin_user.email_change_requested_at = now - timedelta(days=200)
        admin_user.save(update_fields=['email_change_requested_at'])

        result = User.objects.process_email_change_lifecycle(now=now)

        test_user.refresh_from_db()
        admin_user.refresh_from_db()
        assert result == {
            'started': 0,
            'deactivated': 1,
            'deleted': 0,
            'reverified': 0,
            'reactivated': 0,
        }
        assert test_user.is_active is False
        assert test_user.email_change_deactivated_at == now
        assert not Token.objects.filter(pk=token.pk).exists()
        assert admin_user.is_active is True
        assert User.objects.filter(pk=admin_user.pk).exists()
        assert superuser.is_active is False

        test_user.email_change_deactivated_at = now - timedelta(days=98)
        test_user.save(update_fields=['email_change_deactivated_at'])
        result = User.objects.process_email_change_lifecycle(now=now)

        assert result == {
            'started': 0,
            'deactivated': 0,
            'deleted': 1,
            'reverified': 0,
            'reactivated': 0,
        }
        assert not User.objects.filter(pk=test_user.pk).exists()
        assert User.objects.filter(pk=admin_user.pk).exists()
        assert User.objects.filter(pk=superuser.pk).exists()

    def test_email_lifecycle_clears_timer_after_manual_admin_verification(self, test_user):
        from allauth.account.models import EmailAddress

        now = timezone.now()
        test_user.email_change_requested_at = now - timedelta(days=40)
        test_user.email_change_deactivated_at = now - timedelta(days=9)
        test_user.email_change_original_email = 'old@example.com'
        test_user.is_active = False
        test_user.save(update_fields=[
            'email_change_requested_at',
            'email_change_deactivated_at',
            'email_change_original_email',
            'is_active',
        ])
        EmailAddress.objects.create(
            user=test_user,
            email='old@example.com',
            primary=False,
            verified=False,
        )
        EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            primary=True,
            verified=True,
        )

        result = User.objects.process_email_change_lifecycle(now=now)

        test_user.refresh_from_db()
        assert result == {
            'started': 0,
            'deactivated': 0,
            'deleted': 0,
            'reverified': 1,
            'reactivated': 1,
        }
        assert test_user.is_active is True
        assert test_user.email_change_requested_at is None
        assert test_user.email_change_deactivated_at is None

    def test_email_lifecycle_keeps_pending_change_when_old_address_is_verified(self, test_user):
        from allauth.account.models import EmailAddress

        now = timezone.now()
        test_user.email_change_requested_at = now - timedelta(days=1)
        test_user.email_change_original_email = test_user.email
        test_user.save(update_fields=['email_change_requested_at', 'email_change_original_email'])
        EmailAddress.objects.create(
            user=test_user,
            email=test_user.email,
            primary=True,
            verified=True,
        )
        EmailAddress.objects.create(
            user=test_user,
            email='new-address@example.com',
            primary=False,
            verified=False,
        )

        result = User.objects.process_email_change_lifecycle(now=now)

        test_user.refresh_from_db()
        assert result == {
            'started': 0,
            'deactivated': 0,
            'deleted': 0,
            'reverified': 0,
            'reactivated': 0,
        }
        assert test_user.is_active is True
        assert test_user.email_change_requested_at == now - timedelta(days=1)

    def test_create_default_superuser_command(self, monkeypatch, db):
        monkeypatch.setenv('DJANGO_SUPERUSER_USERNAME', 'superadmin')
        monkeypatch.setenv('DJANGO_SUPERUSER_EMAIL', 'superadmin@example.com')
        monkeypatch.setenv('DJANGO_SUPERUSER_PASSWORD', 'StrongPass123!')

        call_command('create_default_superuser')

        user = User.objects.get(username='superadmin')
        assert user.email == 'superadmin@example.com'
        assert user.is_superuser is True
        assert user.check_password('StrongPass123!') is True
