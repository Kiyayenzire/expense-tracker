from datetime import timedelta

from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.utils import timezone


def user_profile_picture_upload_path(instance, filename):
    return f'profile_pictures/{instance.username}/{filename}'


class UserManager(DjangoUserManager):
    def get_by_natural_key(self, username):
        return self.get(**{f'{self.model.USERNAME_FIELD}__iexact': username})

    def delete_expired_account_deletions(self):
        cutoff = timezone.now() - timedelta(days=31)
        expired_users = self.filter(account_deletion_requested_at__lt=cutoff)
        count = expired_users.count()
        expired_users.delete()
        return count

    def process_email_change_lifecycle(self, now=None):
        now = now or timezone.now()
        from allauth.account.models import EmailAddress

        untracked_users = self.filter(
            email_change_requested_at__isnull=True,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        ).exclude(email='')
        started_count = 0
        for user in untracked_users.iterator():
            has_verified_current_email = EmailAddress.objects.filter(
                user=user,
                email__iexact=user.email,
                verified=True,
            ).exists()
            if not has_verified_current_email:
                self.filter(pk=user.pk, email_change_requested_at__isnull=True).update(
                    email_change_requested_at=now,
                    email_change_original_email=user.email,
                )
                started_count += 1

        eligible_users = self.filter(
            email_change_requested_at__isnull=False,
            is_staff=False,
            is_superuser=False,
        )
        reverified_count = 0
        reactivated_count = 0
        for user in eligible_users.iterator():
            was_deactivated = user.email_change_deactivated_at is not None
            if user.reconcile_email_change_verification():
                reverified_count += 1
                if was_deactivated:
                    reactivated_count += 1

        expiration = now - timedelta(days=31)
        deactivated_users = self.filter(
            email_change_requested_at__lte=expiration,
            email_change_deactivated_at__isnull=True,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        deactivated_ids = list(deactivated_users.values_list('pk', flat=True))
        if deactivated_ids:
            deactivated_users.update(is_active=False, email_change_deactivated_at=now)
            from rest_framework.authtoken.models import Token
            Token.objects.filter(user_id__in=deactivated_ids).delete()

        deletion_cutoff = now - timedelta(days=97)
        expired_accounts = self.filter(
            email_change_deactivated_at__lte=deletion_cutoff,
            is_staff=False,
            is_superuser=False,
        )
        deleted_count = expired_accounts.count()
        expired_accounts.delete()
        return {
            'started': started_count,
            'deactivated': len(deactivated_ids),
            'deleted': deleted_count,
            'reverified': reverified_count,
            'reactivated': reactivated_count,
        }


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone_number = models.CharField(max_length=32, blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text='Optional monthly income used for budget recommendations.')
    profile_picture = models.ImageField(
        upload_to=user_profile_picture_upload_path,
        blank=True,
        null=True,
        default=None,
        help_text='Optional profile photo for the account.'
    )
    two_factor_enabled = models.BooleanField(default=False)
    account_deletion_requested_at = models.DateTimeField(blank=True, null=True)
    email_change_requested_at = models.DateTimeField(blank=True, null=True)
    email_change_deactivated_at = models.DateTimeField(blank=True, null=True)
    email_change_original_email = models.EmailField(blank=True, default='')

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.email:
            normalized_email = self.email.strip().lower()
            if normalized_email != self.email:
                self.email = normalized_email
                update_fields = kwargs.get('update_fields')
                if update_fields is not None:
                    kwargs['update_fields'] = set(update_fields) | {'email'}
        return super().save(*args, **kwargs)

    @property
    def is_account_deletion_pending(self):
        return self.account_deletion_requested_at is not None

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser

    def request_account_deletion(self, password):
        if not self.check_password(password):
            raise ValueError('Password is incorrect.')

        if self.is_account_deletion_pending:
            raise ValueError('An account deletion request is already pending.')

        self.account_deletion_requested_at = timezone.now()
        self.save(update_fields=['account_deletion_requested_at'])
        return self

    def cancel_account_deletion(self):
        self.account_deletion_requested_at = None
        self.save(update_fields=['account_deletion_requested_at'])
        return self

    @property
    def email_change_deadline(self):
        if self.email_change_requested_at is None:
            return None
        return self.email_change_requested_at + timedelta(days=31)

    def deactivate_if_email_change_expired(self, now=None):
        if (
            self.email_change_requested_at is None
            or self.email_change_deactivated_at is not None
            or self.is_staff
            or self.is_superuser
            or (now or timezone.now()) < self.email_change_deadline
        ):
            return False
        self.is_active = False
        self.email_change_deactivated_at = now or timezone.now()
        self.save(update_fields=['is_active', 'email_change_deactivated_at'])
        from rest_framework.authtoken.models import Token
        Token.objects.filter(user=self).delete()
        return True

    def reconcile_email_change_verification(self):
        if self.email_change_requested_at is None:
            return False

        from allauth.account.models import EmailAddress

        addresses = EmailAddress.objects.filter(user=self)
        has_verified_current_email = addresses.filter(
            email__iexact=self.email,
            verified=True,
        ).exists()
        email_was_manually_updated = bool(
            self.email_change_original_email
            and self.email.lower() != self.email_change_original_email.lower()
        )
        has_unverified_change = addresses.filter(verified=False).exclude(
            email__iexact=self.email,
        ).exists()
        if not has_verified_current_email or (has_unverified_change and not email_was_manually_updated):
            return False

        self.email_change_requested_at = None
        self.email_change_deactivated_at = None
        self.email_change_original_email = ''
        update_fields = [
            'email_change_requested_at',
            'email_change_deactivated_at',
            'email_change_original_email',
        ]
        if not self.is_active:
            self.is_active = True
            update_fields.append('is_active')
        self.save(update_fields=update_fields)
        return True

    def start_email_change_deadline_if_unverified(self, now=None):
        if (
            self.email_change_requested_at is not None
            or not self.is_active
            or self.is_staff
            or self.is_superuser
            or not self.email
        ):
            return False
        from allauth.account.models import EmailAddress
        if EmailAddress.objects.filter(
            user=self,
            email__iexact=self.email,
            verified=True,
        ).exists():
            return False
        self.email_change_requested_at = now or timezone.now()
        self.email_change_original_email = self.email
        self.save(update_fields=['email_change_requested_at', 'email_change_original_email'])
        return True
