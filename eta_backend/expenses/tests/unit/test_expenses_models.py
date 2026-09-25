from decimal import Decimal
from datetime import date

import pytest

from expenses.models import ExpenseEntry


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
