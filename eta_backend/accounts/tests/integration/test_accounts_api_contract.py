from datetime import date

import pytest
from rest_framework import status


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsLoginAPIContract:
    def test_login_requires_credentials(self, api_client):
        response = api_client.post('/api/auth/login/', {'username': '', 'password': ''})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success_for_registered_user(self, api_client, test_user):
        response = api_client.post('/api/auth/login/', {'username': 'testuser', 'password': 'testpass123'})
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert 'key' in payload
        assert 'user' in payload

    def test_login_fails_for_invalid_password(self, api_client, test_user):
        response = api_client.post('/api/auth/login/', {'username': 'testuser', 'password': 'wrongpass'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsProfileAPIContract:
    def test_profile_requires_auth(self, api_client):
        response = api_client.get('/api/auth/profile/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_returns_authenticated_user(self, authenticated_client, test_user):
        response = authenticated_client.get('/api/auth/profile/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['username'] == 'testuser'

    def test_profile_patch_updates_fields(self, authenticated_client, test_user):
        payload = {'first_name': 'Jane', 'last_name': 'Doe', 'phone_number': '0700000000'}
        response = authenticated_client.patch('/api/auth/profile/', payload, format='multipart')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['first_name'] == 'Jane'
        assert data['last_name'] == 'Doe'
        assert data['phone_number'] == '0700000000'


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsPasswordResetAPIContract:
    def test_password_reset_request_accepts_email(self, api_client):
        response = api_client.post('/api/auth/password/reset/', {'email': 'test@example.com'})
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_confirm_requires_fields(self, api_client):
        response = api_client.post('/api/auth/password/reset/confirm/', {'uid': '', 'token': '', 'new_password': ''})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.django_db
class TestAccountsDeletionAPIContract:
    def test_account_deletion_requires_password(self, authenticated_client):
        response = authenticated_client.post('/api/auth/delete-account/', {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_account_deletion_marks_pending_state(self, authenticated_client, test_user):
        response = authenticated_client.post('/api/auth/delete-account/', {'password': 'testpass123'})
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['pending_deletion'] is True
