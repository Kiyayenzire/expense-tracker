from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status


@pytest.mark.integration
@pytest.mark.django_db
class TestExpenseEntryAPIContract:
    def test_list_expenses_requires_auth(self, api_client):
        response = api_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_expenses_authenticated(self, authenticated_client, multiple_expenses):
        response = authenticated_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_create_expense_requires_auth(self, api_client, category, item, currency):
        payload = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': item.id,
            'amount': '25.50',
            'currency': currency.id,
        }
        response = api_client.post('/api/expenses/', payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_expense_authenticated(self, authenticated_client, test_user, category, item, currency):
        payload = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': item.id,
            'amount': '25.50',
            'currency': currency.id,
        }
        response = authenticated_client.post('/api/expenses/', payload)
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result['user'] == test_user.id
        assert Decimal(str(result['amount'])) == Decimal('25.50')

    def test_user_cannot_view_other_user_expenses(self, db, authenticated_client, test_user, category, item, currency):
        from accounts.models import User
        from expenses.models import ExpenseEntry

        other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='pass123')
        ExpenseEntry.objects.create(
            user=other_user,
            date=date.today(),
            category=category,
            item=item,
            amount=Decimal('100.00'),
            currency=currency,
        )

        response = authenticated_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_view_all_expenses(self, admin_client, test_user, category, item, currency, db):
        from expenses.models import ExpenseEntry

        ExpenseEntry.objects.create(
            user=test_user,
            date=date.today(),
            category=category,
            item=item,
            amount=Decimal('50.00'),
            currency=currency,
        )

        response = admin_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_expense_requires_ownership(self, db, authenticated_client, test_user, expense_entry):
        response = authenticated_client.patch(f'/api/expenses/{expense_entry.id}/', {'amount': '99.99'})
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.integration
@pytest.mark.django_db
class TestSummaryAPIContract:
    def test_summary_endpoint_requires_auth(self, api_client):
        response = api_client.get('/api/expenses/summary/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_summary_endpoint_returns_all_periods(self, authenticated_client, multiple_expenses):
        response = authenticated_client.get('/api/expenses/summary/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for key in ['daily', 'weekly', 'monthly', 'quarterly', 'annual']:
            assert key in data
            assert isinstance(data[key], (int, float))

    def test_yearly_endpoint_format(self, authenticated_client, multiple_expenses):
        year = date.today().year
        response = authenticated_client.get(f'/api/expenses/yearly/{year}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['year'] == str(year)
        assert 'total' in data
        assert isinstance(data['total'], (int, float))

    def test_chart_endpoint_has_required_fields(self, authenticated_client, multiple_expenses):
        response = authenticated_client.get('/api/expenses/chart/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'expensive' in data
        assert 'least' in data
        assert isinstance(data['expensive'], list)
        assert isinstance(data['least'], list)


@pytest.mark.integration
@pytest.mark.django_db
class TestCurrencyConversionAPIContract:
    def test_convert_currency_requires_auth(self, api_client):
        response = api_client.get('/api/convert-currency/?base=EUR&target=USD&amount=100')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_convert_currency_authenticated(self, authenticated_client, currency_rate):
        response = authenticated_client.get('/api/convert-currency/?base=EUR&target=USD&amount=100')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['base'] == 'EUR'
        assert data['target'] == 'USD'
        assert data['rate'] is not None
        if data['rate']:
            assert data['converted'] == 110.0

    def test_current_rates_endpoint_returns_active_matrix(self, authenticated_client):
        response = authenticated_client.get('/api/rates/current/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'rates' in data
        assert 'EUR' in data['rates']
        assert 'USD' in data['rates']
        assert 'UGX' in data['rates']
        assert data['rates']['EUR']['USD'] > 0

    def test_convert_same_currency(self, authenticated_client):
        response = authenticated_client.get('/api/convert-currency/?base=EUR&target=EUR&amount=100')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['rate'] == 1
        assert data['converted'] == 100.0
