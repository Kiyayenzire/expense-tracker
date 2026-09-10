import pytest

from accounts.models import User


pytestmark = pytest.mark.django_db


ADMIN_URL = '/admin/'


def test_regular_user_cannot_access_admin(client):
    user = User.objects.create_user(username='regular-user', password='StrongPass123!')
    client.force_login(user)

    response = client.get(ADMIN_URL)

    assert response.status_code == 403


def test_superuser_can_access_admin(client):
    user = User.objects.create_superuser(
        username='superuser',
        email='superuser@example.com',
        password='StrongPass123!',
    )
    client.force_login(user)

    response = client.get(ADMIN_URL)

    assert response.status_code == 200


def test_custom_admin_url_is_not_available(client):
    response = client.get('/eta-thech@2026/')

    assert response.status_code == 404