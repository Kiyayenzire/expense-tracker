import pytest
from datetime import date, timedelta
from decimal import Decimal
from django.core.management import call_command

from expenses.models import Category, Currency, CurrencyRate, Item, SubCategory


@pytest.mark.unit
@pytest.mark.django_db
def test_seed_command_adds_transport_and_health_subcategories_idempotently():
    expected_subcategories = {
        'Transport': {'Boda Boda', 'Fuel', 'Car Insurance', 'Repairs', 'Tires'},
        'Health Care': {'Health Insurance', 'Tests', 'Supplements'},
    }
    transport = Category.objects.create(name='Transport')
    old_boda_boda = SubCategory.objects.create(name='Boda Boda Transport', category=transport)
    Item.objects.create(description='Boda Boda Transport', category=transport, subcategory=old_boda_boda, measurement='un')

    call_command('seed_initial_data')

    for category_name, subcategory_names in expected_subcategories.items():
        category = Category.objects.get(name=category_name)
        assert set(category.subcategories.values_list('name', flat=True)) >= subcategory_names
        assert set(Item.objects.filter(category=category).values_list('description', flat=True)) >= subcategory_names
    assert not transport.subcategories.filter(name='Boda Boda Transport').exists()
    fuel = transport.subcategories.get(name='Fuel')
    assert Item.objects.get(category=transport, subcategory=fuel).measurement == 'ltr'

    call_command('seed_initial_data')

    for category_name, subcategory_names in expected_subcategories.items():
        category = Category.objects.get(name=category_name)
        assert category.subcategories.filter(name__in=subcategory_names).count() == len(subcategory_names)


@pytest.mark.unit
@pytest.mark.django_db
def test_seed_command_preserves_existing_currency_rates():
    call_command('seed_initial_data')
    ugx = Currency.objects.get(code='UGX')
    eur = Currency.objects.get(code='EUR')
    rate = CurrencyRate.objects.get(
        base_currency=ugx,
        target_currency=eur,
        effective_date=date.today(),
    )
    rate.rate = Decimal('0.0002300000000')
    rate.is_manual = True
    rate.effective_date = date.today() - timedelta(days=1)
    rate.save()

    call_command('seed_initial_data')

    rate.refresh_from_db()
    assert rate.rate == Decimal('0.0002300000000')
    assert rate.is_manual
    assert not CurrencyRate.objects.filter(
        base_currency=ugx,
        target_currency=eur,
        effective_date=date.today(),
    ).exists()