from decimal import Decimal
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from expenses.models import Category, Currency, CurrencyRate, ExpenseEntry, Item, SubCategory

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(username='testuser', email='test@example.com', password='testpass123', role='user')


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='adminuser',
        email='admin@example.com',
        password='adminpass123',
        role='admin',
        is_staff=True,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def category(db):
    return Category.objects.create(name='Groceries', color='#10B981', is_active=True)


@pytest.fixture
def multiple_categories(db):
    return [
        Category.objects.create(name='Food', color='#10B981', is_active=True),
        Category.objects.create(name='Transport', color='#3B82F6', is_active=True),
        Category.objects.create(name='Entertainment', color='#F59E0B', is_active=True),
        Category.objects.create(name='Utilities', color='#EF4444', is_active=True),
    ]


@pytest.fixture
def subcategory(db, category):
    return SubCategory.objects.create(name='Vegetables', category=category)


@pytest.fixture
def item(db, category, subcategory):
    return Item.objects.create(description='Tomatoes', category=category, subcategory=subcategory, measurement='kg')


@pytest.fixture
def currency(db):
    return Currency.objects.create(code='EUR', name='Euro', symbol='€', is_active=True)


@pytest.fixture
def usd_currency(db):
    return Currency.objects.create(code='USD', name='US Dollar', symbol='$', is_active=True)


@pytest.fixture
def currency_rate(db, currency, usd_currency):
    return CurrencyRate.objects.create(
        base_currency=currency,
        target_currency=usd_currency,
        rate=Decimal('1.10'),
        effective_date=date.today(),
    )


@pytest.fixture
def expense_entry(db, test_user, category, item, subcategory, currency):
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
        notes='Weekly groceries',
    )


@pytest.fixture
def multiple_expenses(db, test_user, category, item, currency):
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
            notes=f'Expense {i + 1}',
        )
        expenses.append(expense)
    return expenses
