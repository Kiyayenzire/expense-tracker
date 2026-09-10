import pytest
from rest_framework.test import APIClient

from expenses.models import Category, SubCategory


@pytest.mark.integration
@pytest.mark.django_db
def test_quick_entry_api_returns_reviewable_draft(test_user, currency):
    category = Category.objects.create(name='Food', color='#10B981')
    SubCategory.objects.create(name='Restaurants', category=category)
    client = APIClient()
    client.force_authenticate(user=test_user)

    response = client.post('/api/expenses/parse-quick-entry/', {
        'text': 'I spent 35 EUR at Java House for lunch',
    }, format='json')

    assert response.status_code == 200
    assert response.data['amount'] == '35.00'
    assert response.data['currency'] == 'EUR'
    assert response.data['category'] == category.id
    assert response.data['needs_confirmation'] is True
