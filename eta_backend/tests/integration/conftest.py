"""Pytest configuration for integration tests."""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def test_client():
    """Fixture for test API client."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(test_client, test_user):
    """Fixture for authenticated API client in integration tests."""
    test_client.force_authenticate(user=test_user)
    return test_client

