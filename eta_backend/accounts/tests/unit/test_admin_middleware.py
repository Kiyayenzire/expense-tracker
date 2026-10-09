from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse, HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse
import pytest
import time

from accounts.middleware import SuperuserAdminMiddleware

User = get_user_model()


@pytest.mark.django_db
class TestSuperuserAdminMiddleware:
    def make_request(self, request_method, path, user, backend=None):
        request = RequestFactory().generic(request_method, path)
        request.session = SessionStore()
        request.session.create()
        if backend:
            request.session['_auth_user_backend'] = backend
        request.user = user
        return request

    def create_superuser(self, username):
        return User.objects.create_superuser(
            username=username,
            email=f'{username}@example.com',
            password='StrongPassword1!',
        )

    def test_social_session_is_redirected_to_admin_password_login(self):
        superuser = self.create_superuser('social-admin')
        request = self.make_request(
            'GET',
            reverse('admin:index'),
            superuser,
            backend='allauth.account.auth_backends.AuthenticationBackend',
        )
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))

        response = middleware(request)

        assert response.status_code == 302
        assert response.url.startswith(reverse('admin:login'))

    def test_admin_password_post_marks_session_and_grants_access(self):
        superuser = self.create_superuser('password-admin')
        request = self.make_request(
            'POST',
            reverse('admin:login'),
            AnonymousUser(),
        )

        def authenticate_admin_password(request):
            user = authenticate(
                request,
                username=superuser.username,
                password='StrongPassword1!',
            )
            if user is None:
                return HttpResponse(status=200)
            login(request, user)
            return HttpResponseRedirect(reverse('admin:index'))

        middleware = SuperuserAdminMiddleware(
            authenticate_admin_password
        )

        login_response = middleware(request)
        admin_request = self.make_request('GET', reverse('admin:index'), superuser)
        admin_request.session = request.session
        admin_middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))
        admin_response = admin_middleware(admin_request)

        assert login_response.status_code == 302
        assert request.session.get(middleware.ADMIN_AUTH_SESSION_KEY) == request.session.session_key
        assert request.session.get(middleware.ADMIN_LAST_ACTIVITY_SESSION_KEY) is not None
        assert admin_response.status_code == 200

    def test_session_rotation_invalidates_admin_password_grant(self):
        superuser = self.create_superuser('rotated-admin')
        login_request = self.make_request(
            'POST',
            reverse('admin:login'),
            superuser,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        login_middleware = SuperuserAdminMiddleware(
            lambda request: HttpResponseRedirect(reverse('admin:index'))
        )
        login_middleware(login_request)
        login_request.session.cycle_key()

        admin_request = self.make_request('GET', reverse('admin:index'), superuser)
        admin_request.session = login_request.session
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))
        response = middleware(admin_request)

        assert response.status_code == 302
        assert response.url.startswith(reverse('admin:login'))

    def test_app_password_session_does_not_authorize_admin_access(self):
        superuser = self.create_superuser('app-password-admin')
        request = self.make_request(
            'GET',
            reverse('admin:index'),
            superuser,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))

        response = middleware(request)

        assert response.status_code == 302
        assert response.url.startswith(reverse('admin:login'))

    def test_non_superuser_gets_generic_not_found_on_admin_path(self):
        user = User.objects.create_user(
            username='regular-user',
            email='regular@example.com',
            password='StrongPassword1!',
        )
        request = self.make_request('GET', reverse('admin:index'), user)
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))

        response = middleware(request)

        assert response.status_code == 404
        assert b'Only superusers' not in response.content

    def test_authenticated_non_superuser_gets_not_found_on_admin_login_path(self):
        user = User.objects.create_user(
            username='regular-login-user',
            email='regular-login@example.com',
            password='StrongPassword1!',
        )
        request = self.make_request('GET', reverse('admin:login'), user)
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))

        response = middleware(request)

        assert response.status_code == 404

    def test_unverified_superuser_gets_a_clean_admin_login_form(self):
        superuser = self.create_superuser('reauth-admin')
        request = self.make_request(
            'GET',
            reverse('admin:login'),
            superuser,
            backend='allauth.account.auth_backends.AuthenticationBackend',
        )
        middleware = SuperuserAdminMiddleware(
            lambda request: HttpResponse(status=200 if not request.user.is_authenticated else 500)
        )

        response = middleware(request)

        assert response.status_code == 200
        assert not request.user.is_authenticated
        assert request.session['_auth_user_backend'] == 'allauth.account.auth_backends.AuthenticationBackend'

    def test_non_staff_session_cannot_open_admin_login_page(self):
        user = User.objects.create_user(
            username='app-user',
            email='app-user@example.com',
            password='StrongPassword1!',
        )
        request = self.make_request(
            'GET',
            reverse('admin:login'),
            user,
            backend='allauth.account.auth_backends.AuthenticationBackend',
        )
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))

        response = middleware(request)

        assert response.status_code == 404
        assert request.user.is_authenticated

    def test_admin_session_expires_after_eleven_minutes_of_inactivity(self, monkeypatch):
        monkeypatch.setattr('accounts.middleware.time.time', lambda: 1000)
        superuser = self.create_superuser('idle-admin')
        request = self.make_request('GET', reverse('admin:index'), superuser)
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))
        request.session[middleware.ADMIN_AUTH_SESSION_KEY] = request.session.session_key
        request.session[middleware.ADMIN_LAST_ACTIVITY_SESSION_KEY] = (
            1000 - middleware.ADMIN_IDLE_TIMEOUT_SECONDS
        )

        response = middleware(request)

        assert response.status_code == 302
        assert response.url.startswith(reverse('admin:login'))
        assert not request.user.is_authenticated
        assert middleware.ADMIN_AUTH_SESSION_KEY not in request.session

    def test_admin_activity_refreshes_idle_timeout(self, monkeypatch):
        monkeypatch.setattr('accounts.middleware.time.time', lambda: 1000)
        superuser = self.create_superuser('active-admin')
        request = self.make_request('GET', reverse('admin:index'), superuser)
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))
        request.session[middleware.ADMIN_AUTH_SESSION_KEY] = request.session.session_key
        request.session[middleware.ADMIN_LAST_ACTIVITY_SESSION_KEY] = 999

        response = middleware(request)

        assert response.status_code == 200
        assert request.session[middleware.ADMIN_LAST_ACTIVITY_SESSION_KEY] == 1000

    def test_expired_admin_session_shows_login_without_redirect_loop(self, monkeypatch):
        monkeypatch.setattr('accounts.middleware.time.time', lambda: 1000)
        superuser = self.create_superuser('expired-login-admin')
        request = self.make_request('GET', reverse('admin:login'), superuser)
        middleware = SuperuserAdminMiddleware(
            lambda request: HttpResponse(status=200 if not request.user.is_authenticated else 500)
        )
        request.session[middleware.ADMIN_AUTH_SESSION_KEY] = request.session.session_key
        request.session[middleware.ADMIN_LAST_ACTIVITY_SESSION_KEY] = (
            1000 - middleware.ADMIN_IDLE_TIMEOUT_SECONDS
        )

        response = middleware(request)

        assert response.status_code == 200
        assert not request.user.is_authenticated
        assert middleware.ADMIN_AUTH_SESSION_KEY not in request.session

    def test_non_admin_request_does_not_refresh_admin_idle_timeout(self, monkeypatch):
        monkeypatch.setattr('accounts.middleware.time.time', lambda: 1000)
        superuser = self.create_superuser('api-admin')
        request = self.make_request('GET', '/api/auth/profile/', superuser)
        middleware = SuperuserAdminMiddleware(lambda request: HttpResponse(status=200))
        request.session[middleware.ADMIN_AUTH_SESSION_KEY] = request.session.session_key
        request.session[middleware.ADMIN_LAST_ACTIVITY_SESSION_KEY] = 999

        response = middleware(request)

        assert response.status_code == 200
        assert request.session[middleware.ADMIN_LAST_ACTIVITY_SESSION_KEY] == 999