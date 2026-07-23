"""Root pytest configuration for ETA application tests."""
import sys
import os
import django
from pathlib import Path
from decimal import Decimal

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

django.setup()

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from expenses.models import Category, SubCategory, Item, Currency, ExpenseEntry, CurrencyRate
from datetime import date, timedelta

User = get_user_model()


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "django_db: mark test as requiring database"
    )


# Session fixtures
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup):
    """Setup Django test database."""
    pass


# User fixtures
@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role='user'
    )


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        role='admin',
        is_staff=True
    )


# API Client fixtures
@pytest.fixture
def api_client():
    """Create an API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Create an authenticated API client."""
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Create an authenticated admin API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client


# Model fixtures
@pytest.fixture
def category(db):
    """Create a test category."""
    return Category.objects.create(
        name='Groceries',
        color='#10B981',
        is_active=True
    )


@pytest.fixture
def multiple_categories(db):
    """Create multiple test categories."""
    categories = [
        Category.objects.create(name='Food', color='#10B981'),
        Category.objects.create(name='Transport', color='#3B82F6'),
        Category.objects.create(name='Entertainment', color='#F59E0B'),
        Category.objects.create(name='Utilities', color='#EF4444'),
    ]
    return categories


@pytest.fixture
def subcategory(db, category):
    """Create a test subcategory."""
    return SubCategory.objects.create(
        name='Vegetables',
        category=category
    )


@pytest.fixture
def item(db, category, subcategory):
    """Create a test item."""
    return Item.objects.create(
        description='Tomatoes',
        category=category,
        subcategory=subcategory
    )


@pytest.fixture
def currency(db):
    """Create a test currency."""
    return Currency.objects.create(
        code='EUR',
        name='Euro',
        symbol='€',
        is_active=True
    )


@pytest.fixture
def usd_currency(db):
    """Create USD currency."""
    return Currency.objects.create(
        code='USD',
        name='US Dollar',
        symbol='$',
        is_active=True
    )


@pytest.fixture
def currency_rate(db, currency, usd_currency):
    """Create a test currency rate."""
    return CurrencyRate.objects.create(
        base_currency=currency,
        target_currency=usd_currency,
        rate=Decimal('1.10'),
        effective_date=date.today()
    )


@pytest.fixture
def expense_entry(db, test_user, category, item, subcategory, currency):
    """Create a test expense entry."""
    return ExpenseEntry.objects.create(
        user=test_user,
        date=date.today(),
        category=category,
        item=item,
        subcategory=subcategory,
        quantity=Decimal('2.5'),
        supplier='Local Market',
        country='Italy',
        amount=Decimal('25.50'),
        currency=currency,
        notes='Weekly groceries'
    )


@pytest.fixture
def multiple_expenses(db, test_user, category, item, currency):
    """Create multiple expense entries for testing."""
    today = date.today()
    expenses = []
    for i in range(10):
        expense = ExpenseEntry.objects.create(
            user=test_user,
            date=today - timedelta(days=i),
            category=category,
            item=item,
            quantity=Decimal('1'),
            amount=Decimal(f'{10 + i * 2}'),
            currency=currency,
            notes=f'Expense {i+1}'
        )
        expenses.append(expense)
    return expenses
