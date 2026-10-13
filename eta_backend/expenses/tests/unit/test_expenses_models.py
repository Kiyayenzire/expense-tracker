from decimal import Decimal
from datetime import date, timedelta

import pytest

from expenses.models import Currency, CurrencyRate, ExpenseEntry


@pytest.mark.unit
@pytest.mark.django_db
class TestExpenseEntryModel:
    def test_create_expense_entry(self, expense_entry):
        assert expense_entry.user.username == 'testuser'
        assert expense_entry.category.name == 'Groceries'
        assert expense_entry.amount == Decimal('25.50')
        assert expense_entry.quantity == Decimal('2.5')

    def test_expense_entry_string_representation(self, expense_entry):
        expected = f'{date.today()} Groceries 25.50 EUR'
        assert str(expense_entry) == expected

    def test_expense_entry_ordering(self, multiple_expenses):
        entries = ExpenseEntry.objects.all()
        dates = [entry.date for entry in entries]
        assert dates == sorted(dates, reverse=True)

    def test_expense_entry_default_quantity(self, db, test_user, category, item, currency):
        expense = ExpenseEntry.objects.create(
            user=test_user,
            date=date.today(),
            category=category,
            item=item,
            amount=Decimal('10'),
            currency=currency,
        )
        assert expense.quantity == Decimal('1')

    def test_new_expense_prefers_manual_rate_over_newer_weekly_snapshot(
        self, db, test_user, category, item
    ):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        ugx = Currency.objects.create(code='UGX', name='Ugandan Shilling')
        eur = Currency.objects.create(code='EUR', name='Euro')
        CurrencyRate.objects.create(
            base_currency=ugx,
            target_currency=eur,
            rate=Decimal('0.0002500000000'),
            effective_date=week_start + timedelta(days=1),
            is_manual=True,
        )
        CurrencyRate.objects.create(
            base_currency=ugx,
            target_currency=eur,
            rate=Decimal('0.0002000000000'),
            effective_date=week_start + timedelta(days=2),
        )
        expense = ExpenseEntry.objects.create(
            user=test_user,
            date=week_start + timedelta(days=6),
            category=category,
            item=item,
            amount=Decimal('10000'),
            currency=ugx,
        )

        assert expense.applied_rate_to_eur == Decimal('0.000250')
        assert expense.amount_base_eur == Decimal('2.50')
