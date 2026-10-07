import pytest
from django.core.management import call_command

from expenses.models import Category, Item, SubCategory


@pytest.mark.unit
@pytest.mark.django_db
def test_seed_command_adds_transport_and_health_subcategories_idempotently():
    expected_subcategories = {
        'Transport': {'Boda Boda', 'Car Insurance', 'Repairs', 'Tires'},
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

    call_command('seed_initial_data')

    for category_name, subcategory_names in expected_subcategories.items():
        category = Category.objects.get(name=category_name)
        assert category.subcategories.filter(name__in=subcategory_names).count() == len(subcategory_names)