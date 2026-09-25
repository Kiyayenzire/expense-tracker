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

    def test_create_default_superuser_command(self, monkeypatch, db):
        monkeypatch.setenv('DJANGO_SUPERUSER_USERNAME', 'superadmin')
        monkeypatch.setenv('DJANGO_SUPERUSER_EMAIL', 'superadmin@example.com')
        monkeypatch.setenv('DJANGO_SUPERUSER_PASSWORD', 'StrongPass123!')

        call_command('create_default_superuser')

        user = User.objects.get(username='superadmin')
        assert user.email == 'superadmin@example.com'
        assert user.is_superuser is True
        assert user.check_password('StrongPass123!') is True
