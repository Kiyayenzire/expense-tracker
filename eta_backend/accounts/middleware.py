import time

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.urls import reverse


class SuperuserAdminMiddleware:
    """Restrict Django admin access to superusers verified through its password form."""

    ADMIN_AUTH_SESSION_KEY = '_admin_password_session_key'
    ADMIN_LAST_ACTIVITY_SESSION_KEY = '_admin_last_activity'
    ADMIN_IDLE_TIMEOUT_SECONDS = 11 * 60
    ADMIN_LOGIN_BACKEND = 'django.contrib.auth.backends.ModelBackend'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = f"/{settings.DJANGO_ADMIN_URL.strip('/')}/"
        if request.path != admin_path and not request.path.startswith(admin_path):
            return self.get_response(request)

        admin_login_path = f'{admin_path}login/'
        if request.path == admin_login_path and request.method == 'GET':
            if self._is_admin_session_expired(request):
                logout(request)
            if (
                request.user.is_authenticated
                and request.user.is_active
                and request.user.is_staff
                and not self._has_admin_password_session(request)
            ):
                request.user = AnonymousUser()
            elif request.user.is_authenticated and self._has_admin_password_session(request):
                self._mark_admin_activity(request)
            return self.get_response(request)

        if request.path == admin_login_path and request.method == 'POST':
            response = self.get_response(request)
            user = request.user
            if (
                300 <= response.status_code < 400
                and user.is_authenticated
                and user.is_superuser
                and request.session.get('_auth_user_backend') == self.ADMIN_LOGIN_BACKEND
            ):
                request.session[self.ADMIN_AUTH_SESSION_KEY] = request.session.session_key
                self._mark_admin_activity(request)
            return response

        user = request.user
        if user.is_authenticated:
            if not user.is_superuser:
                return HttpResponseForbidden('Only superusers can access the admin site.')
            if not self._has_admin_password_session(request):
                return redirect_to_login(request.get_full_path(), login_url=reverse('admin:login'))
            if self._is_admin_session_expired(request):
                logout(request)
                return redirect_to_login(request.get_full_path(), login_url=reverse('admin:login'))
            self._mark_admin_activity(request)

        return self.get_response(request)

    def _has_admin_password_session(self, request):
        session_key = request.session.session_key
        return bool(
            session_key
            and request.session.get(self.ADMIN_AUTH_SESSION_KEY) == session_key
        )

    def _is_admin_session_expired(self, request):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return False
        if not self._has_admin_password_session(request):
            return False
        last_activity = request.session.get(self.ADMIN_LAST_ACTIVITY_SESSION_KEY)
        return (
            last_activity is not None
            and time.time() - last_activity >= self.ADMIN_IDLE_TIMEOUT_SECONDS
        )

    def _mark_admin_activity(self, request):
        request.session[self.ADMIN_LAST_ACTIVITY_SESSION_KEY] = time.time()