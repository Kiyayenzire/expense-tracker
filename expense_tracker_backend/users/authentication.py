


from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """Authenticate using email OR username.

    This supports legacy users created via the Django admin (which may not
    have an email set) as well as new users created via the frontend (where
    email is required).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):

        if not username or not password:
            return None

        identifier = username.strip()

        # Try email first (case-insensitive), then fall back to username.
        user = None

        try:
            user = User.objects.get(email__iexact=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username__iexact=identifier)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and user.is_active:
            return user

        return None


