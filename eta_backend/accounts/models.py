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

    objects = UserManager()

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
