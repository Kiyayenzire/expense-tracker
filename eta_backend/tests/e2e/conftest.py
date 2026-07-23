"""Pytest configuration for end-to-end tests."""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def e2e_client():
    """Fixture for API client in e2e tests."""
    return APIClient()


@pytest.fixture
def e2e_authenticated_client(e2e_client, test_user):
    """Fixture for authenticated client for full user workflows."""
    e2e_client.force_authenticate(user=test_user)
    return e2e_client

