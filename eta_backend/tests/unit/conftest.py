"""Pytest configuration for unit tests."""
import pytest
from decimal import Decimal


@pytest.fixture
def mock_expense_data():
    """Fixture for mock expense data."""
    return {
        'amount': Decimal('25.50'),
        'quantity': Decimal('2.5'),
        'currency_code': 'EUR',
        'category': 'Groceries'
    }


@pytest.fixture
def mock_user_data():
    """Fixture for mock user data."""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "user"
    }

