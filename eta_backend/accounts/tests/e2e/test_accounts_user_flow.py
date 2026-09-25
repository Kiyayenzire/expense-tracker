from datetime import date

import pytest
from rest_framework import status


@pytest.mark.e2e
@pytest.mark.django_db
class TestAccountsUserFlow:
    def test_account_registration_and_profile_flow(self, api_client):
        response = api_client.post(
            '/api/auth/registration/',
            {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password1': 'StrongPassword1!',
                'password2': 'StrongPassword1!',
            },
            format='json',
        )
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]

        login_response = api_client.post(
            '/api/auth/login/',
            {'username': 'newuser', 'password': 'StrongPassword1!'},
            format='json',
        )
        assert login_response.status_code == status.HTTP_200_OK

        token = login_response.json()['key']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        profile_response = api_client.get('/api/auth/profile/')
        assert profile_response.status_code == status.HTTP_200_OK

        patch_response = api_client.patch(
            '/api/auth/profile/',
            {'first_name': 'New', 'last_name': 'User', 'phone_number': '0701234567'},
            format='multipart',
        )
        assert patch_response.status_code == status.HTTP_200_OK
        assert patch_response.json()['first_name'] == 'New'

    def test_password_reset_flow(self, api_client, test_user):
        response = api_client.post('/api/auth/password/reset/', {'email': 'test@example.com'})
        assert response.status_code == status.HTTP_200_OK

    def test_delete_account_flow(self, authenticated_client, test_user):
        response = authenticated_client.post('/api/auth/delete-account/', {'password': 'testpass123'})
        assert response.status_code == status.HTTP_200_OK
        payload = response.json()
        assert payload['pending_deletion'] is True
