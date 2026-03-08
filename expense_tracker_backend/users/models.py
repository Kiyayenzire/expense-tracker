

from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class CustomUser(AbstractUser):
    """
    Custom user model.

    Improvements included:
    - Email must be unique (prevents duplicate accounts)
    - activation_token used for email verification
    """

    email = models.EmailField(unique=True)

    activation_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    def __str__(self):
        return self.email


