from decimal import Decimal

import pytest

from expenses.models import Category, SubCategory, ExpenseEntry
from expenses.services.intelligence_service import IntelligenceService


@pytest.mark.unit
@pytest.mark.django_db
def test_quick_entry_parses_amount_currency_date_and_category(test_user, currency):
    category = Category.objects.create(name='Food', color='#10B981')
    SubCategory.objects.create(name='Restaurants', category=category)

    result = IntelligenceService.parse_quick_entry(
        'I spent 35k at Java House for lunch yesterday',
        test_user,
    )

    assert result['amount'] == '35000.00'
    assert result['currency'] == 'EUR'
    assert result['description'] == 'Java House'
    assert result['category'] == category.id
    assert result['needs_confirmation'] is True
    assert not ExpenseEntry.objects.filter(user=test_user).exists()


@pytest.mark.unit
@pytest.mark.django_db
def test_quick_entry_rejects_missing_amount(test_user):
    result = IntelligenceService.parse_quick_entry('Java House lunch', test_user)

    assert result['confidence'] == 0.0
    assert result['errors']


@pytest.mark.unit
@pytest.mark.django_db
def test_financial_insights_identifies_largest_category(test_user, category, currency):
    ExpenseEntry.objects.create(
        user=test_user,
        date='2026-09-01',
        category=category,
        quantity=Decimal('2'),
        amount=Decimal('25'),
        currency=currency,
    )

    insights = IntelligenceService.financial_insights(test_user)

    assert insights
    assert insights[0]['title'] == 'Largest spending category'
    assert category.name in insights[0]['message']
