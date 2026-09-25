from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model

from expenses.models import Category, Currency, CurrencyRate, ExpenseEntry, Item, SubCategory

User = get_user_model()


def make_user(username='testuser', email=None, role='user', **kwargs):
    email = email or f'{username}@example.com'
    return User.objects.create_user(
        username=username,
        email=email,
        password=kwargs.pop('password', 'testpass123'),
        role=role,
        **kwargs,
    )


def make_category(name='Groceries', color='#10B981', is_active=True, **kwargs):
    return Category.objects.create(name=name, color=color, is_active=is_active, **kwargs)


def make_subcategory(category=None, name='Vegetables', **kwargs):
    category = category or make_category()
    return SubCategory.objects.create(name=name, category=category, **kwargs)


def make_item(category=None, description='Tomatoes', measurement='pc', subcategory=None, **kwargs):
    category = category or make_category()
    subcategory = subcategory or make_subcategory(category=category)
    return Item.objects.create(
        description=description,
        measurement=measurement,
        category=category,
        subcategory=subcategory,
        **kwargs,
    )


def make_currency(code='EUR', name='Euro', symbol='€', is_active=True, **kwargs):
    return Currency.objects.create(code=code, name=name, symbol=symbol, is_active=is_active, **kwargs)


def make_rate(base_currency=None, target_currency=None, rate='1.10', effective_date=None, **kwargs):
    base_currency = base_currency or make_currency(code='EUR', name='Euro', symbol='€')
    target_currency = target_currency or make_currency(code='USD', name='US Dollar', symbol='$')
    effective_date = effective_date or date.today()
    return CurrencyRate.objects.create(
        base_currency=base_currency,
        target_currency=target_currency,
        rate=Decimal(str(rate)),
        effective_date=effective_date,
        **kwargs,
    )


def make_expense(user=None, category=None, item=None, currency=None, amount='25.50', date_value=None, **kwargs):
    user = user or make_user()
    category = category or make_category()
    item = item or make_item(category=category)
    currency = currency or make_currency()
    date_value = date_value or date.today()
    return ExpenseEntry.objects.create(
        user=user,
        date=date_value,
        category=category,
        item=item,
        quantity=kwargs.pop('quantity', Decimal('1')),
        supplier=kwargs.pop('supplier', 'Local Market'),
        country=kwargs.pop('country', 'Italy'),
        amount=Decimal(str(amount)),
        currency=currency,
        notes=kwargs.pop('notes', 'Expense'),
        **kwargs,
    )
