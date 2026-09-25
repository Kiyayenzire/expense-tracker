from datetime import date
from decimal import Decimal

import pytest
from rest_framework import status


@pytest.mark.e2e
@pytest.mark.django_db
class TestUserExpenseWorkflow:
    def test_complete_expense_tracking_workflow(self, authenticated_client, test_user, multiple_categories, multiple_expenses, currency):
        category = multiple_categories[0]
        payload = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': 1,
            'quantity': '1',
            'amount': '50.00',
            'currency': currency.id,
            'supplier': 'Test Store',
            'country': 'Italy',
            'notes': 'E2E Test Expense',
        }
        response = authenticated_client.post('/api/expenses/', payload)
        assert response.status_code == status.HTTP_201_CREATED

        response = authenticated_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK

        response = authenticated_client.get('/api/expenses/summary/')
        assert response.status_code == status.HTTP_200_OK
        summary = response.json()
        assert summary['daily'] > 0

        response = authenticated_client.get('/api/expenses/chart/')
        assert response.status_code == status.HTTP_200_OK

        response = authenticated_client.get('/api/expenses/insights/')
        assert response.status_code == status.HTTP_200_OK

        response = authenticated_client.get('/api/expenses/prediction/')
        assert response.status_code == status.HTTP_200_OK

    def test_category_browsing_workflow(self, authenticated_client, multiple_categories):
        response = authenticated_client.get('/api/categories/')
        assert response.status_code == status.HTTP_200_OK
        categories = response.json()
        assert len(categories) > 0

        response = authenticated_client.get('/api/subcategories/')
        assert response.status_code == status.HTTP_200_OK

        response = authenticated_client.get('/api/items/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.django_db
class TestMultiCurrencyWorkflow:
    def test_expense_in_multiple_currencies(self, authenticated_client, test_user, category, item, currency, usd_currency):
        payload_eur = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': item.id,
            'amount': '100.00',
            'currency': currency.id,
        }
        response = authenticated_client.post('/api/expenses/', payload_eur)
        assert response.status_code == status.HTTP_201_CREATED

        payload_usd = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': item.id,
            'amount': '110.00',
            'currency': usd_currency.id,
        }
        response = authenticated_client.post('/api/expenses/', payload_usd)
        assert response.status_code == status.HTTP_201_CREATED

        response = authenticated_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK

    def test_currency_conversion_workflow(self, authenticated_client, currency_rate):
        response = authenticated_client.get('/api/convert-currency/?base=EUR&target=USD&amount=100')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['rate'] == 1.1
        assert data['converted'] == 110.0


@pytest.mark.e2e
@pytest.mark.django_db
class TestReportingWorkflow:
    def test_generate_monthly_report_workflow(self, authenticated_client, test_user, multiple_expenses, currency_rate):
        year = date.today().year
        month = date.today().month

        response = authenticated_client.get('/api/expenses/summary/')
        assert response.status_code == status.HTTP_200_OK
        summary = response.json()
        monthly_total = summary['monthly']
        assert monthly_total >= 0

        response = authenticated_client.get(f'/api/expenses/yearly/{year}/')
        assert response.status_code == status.HTTP_200_OK
        yearly = response.json()
        assert yearly['year'] == str(year)

        payload = {'period': 'monthly', 'month': month, 'year': year, 'target_currency': 'EUR'}
        response = authenticated_client.post('/api/export-report/', payload)
        assert response.status_code == status.HTTP_200_OK
        report = response.json()
        assert report['period'] == 'monthly'
        assert report['year'] == year

    def test_current_rates_and_monthly_report_workflow(self, authenticated_client, multiple_expenses, currency_rate):
        rates_response = authenticated_client.get('/api/rates/current/')
        assert rates_response.status_code == status.HTTP_200_OK
        rates_payload = rates_response.json()
        assert 'rates' in rates_payload
        assert rates_payload['rates']['EUR']['USD'] > 0

        month = date.today().strftime('%Y-%m')
        report_response = authenticated_client.get(f'/api/reports/monthly/?month={month}&currency=EUR')
        assert report_response.status_code == status.HTTP_200_OK
        report_payload = report_response.json()
        assert report_payload['report_currency'] == 'EUR'
        assert 'total_amount' in report_payload
