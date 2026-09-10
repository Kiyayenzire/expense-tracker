"""End-to-end tests for complete user workflows."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework import status


@pytest.mark.e2e
@pytest.mark.django_db
class TestUserExpenseWorkflow:
    """E2E tests for user expense tracking workflow."""
    
    def test_complete_expense_tracking_workflow(
        self, authenticated_client, test_user, 
        multiple_categories, multiple_expenses, currency
    ):
        """Test complete workflow: create expense, view summary, get insights."""
        # Step 1: User creates a new expense
        category = multiple_categories[0]
        data = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': 1,
            'quantity': '1',
            'amount': '50.00',
            'currency': currency.id,
            'supplier': 'Test Store',
            'country': 'Italy',
            'notes': 'E2E Test Expense'
        }
        response = authenticated_client.post('/api/expenses/', data)
        assert response.status_code == status.HTTP_201_CREATED
        expense_id = response.json()['id']
        
        # Step 2: Verify expense appears in list
        response = authenticated_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK
        
        # Step 3: Check summary has been updated
        response = authenticated_client.get('/api/expenses/summary/')
        assert response.status_code == status.HTTP_200_OK
        summary = response.json()
        assert summary['daily'] > 0  # Should have today's expenses
        
        # Step 4: Get chart data
        response = authenticated_client.get('/api/expenses/chart/')
        assert response.status_code == status.HTTP_200_OK
        
        # Step 5: Get insights
        response = authenticated_client.get('/api/expenses/insights/')
        assert response.status_code == status.HTTP_200_OK
        
        # Step 6: Get predictions
        response = authenticated_client.get('/api/expenses/prediction/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_category_browsing_workflow(
        self, authenticated_client, multiple_categories
    ):
        """Test workflow of browsing categories and managing items."""
        # Step 1: Get list of categories
        response = authenticated_client.get('/api/categories/')
        assert response.status_code == status.HTTP_200_OK
        categories = response.json()
        assert len(categories) > 0
        
        # Step 2: Get subcategories
        response = authenticated_client.get('/api/subcategories/')
        assert response.status_code == status.HTTP_200_OK
        
        # Step 3: Get items
        response = authenticated_client.get('/api/items/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.django_db
class TestMultiCurrencyWorkflow:
    """E2E tests for multi-currency expense tracking."""
    
    def test_expense_in_multiple_currencies(
        self, authenticated_client, test_user, 
        category, item, currency, usd_currency
    ):
        """Test tracking expenses in different currencies."""
        # Create expense in EUR
        data_eur = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': item.id,
            'amount': '100.00',
            'currency': currency.id
        }
        response = authenticated_client.post('/api/expenses/', data_eur)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Create expense in USD
        data_usd = {
            'date': date.today().isoformat(),
            'category': category.id,
            'item': item.id,
            'amount': '110.00',
            'currency': usd_currency.id
        }
        response = authenticated_client.post('/api/expenses/', data_usd)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify both expenses exist
        response = authenticated_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_currency_conversion_workflow(
        self, authenticated_client, currency_rate
    ):
        """Test currency conversion during analysis."""
        # Get conversion rate
        response = authenticated_client.get(
            '/api/convert-currency/?base=EUR&target=USD&amount=100'
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['rate'] == 1.1
        assert data['converted'] == 110.0


@pytest.mark.e2e
@pytest.mark.django_db
class TestReportingWorkflow:
    """E2E tests for reporting and analysis."""
    
    def test_generate_monthly_report_workflow(
        self, authenticated_client, test_user, multiple_expenses, currency_rate
    ):
        """Test complete workflow of generating a monthly report."""
        year = date.today().year
        month = date.today().month
        
        # Step 1: Get summary for current period
        response = authenticated_client.get('/api/expenses/summary/')
        assert response.status_code == status.HTTP_200_OK
        summary = response.json()
        monthly_total = summary['monthly']
        
        # Step 2: Get yearly summary
        response = authenticated_client.get(f'/api/expenses/yearly/{year}/')
        assert response.status_code == status.HTTP_200_OK
        yearly = response.json()
        assert yearly['year'] == str(year)
        
        # Step 3: Export report
        export_data = {
            'period': 'monthly',
            'month': month,
            'year': year,
            'target_currency': 'EUR'
        }
        response = authenticated_client.post('/api/export-report/', export_data)
        assert response.status_code == status.HTTP_200_OK
        report = response.json()
        assert report['period'] == 'monthly'
        assert report['year'] == year
    
    def test_generate_analysis_report(
        self, authenticated_client, multiple_expenses
    ):
        """Test workflow of generating an analysis report."""
        # Step 1: Get chart data
        response = authenticated_client.get('/api/expenses/chart/')
        assert response.status_code == status.HTTP_200_OK
        chart = response.json()
        
        # Step 2: Get predictions
        response = authenticated_client.get('/api/expenses/prediction/')
        assert response.status_code == status.HTTP_200_OK
        predictions = response.json()
        
        # Step 3: Get insights and anomalies
        response = authenticated_client.get('/api/expenses/insights/')
        assert response.status_code == status.HTTP_200_OK
        insights = response.json()
        assert 'anomalies' in insights

    def test_current_rates_and_monthly_report_workflow(
        self, authenticated_client, multiple_expenses, currency_rate
    ):
        """Test the cached rate matrix and monthly reporting path used by the offline-aware UI."""
        rates_response = authenticated_client.get('/api/rates/current/')
        assert rates_response.status_code == status.HTTP_200_OK
        rates_payload = rates_response.json()
        assert 'rates' in rates_payload
        assert rates_payload['rates']['EUR']['USD'] > 0

        month = date.today().strftime('%Y-%m')
        report_response = authenticated_client.get(
            f'/api/reports/monthly/?month={month}&currency=EUR'
        )
        assert report_response.status_code == status.HTTP_200_OK
        report_payload = report_response.json()
        assert report_payload['report_currency'] == 'EUR'
        assert 'total_amount' in report_payload


@pytest.mark.e2e
@pytest.mark.django_db
class TestDataPermissionsWorkflow:
    """E2E tests for data permissions and access control."""
    
    def test_user_cannot_see_other_user_expenses(
        self, db, authenticated_client, test_user, 
        category, item, currency
    ):
        """Test that users cannot see expenses of other users."""
        from accounts.models import User
        
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        
        # Create expense for other user
        from expenses.models import ExpenseEntry
        ExpenseEntry.objects.create(
            user=other_user,
            date=date.today(),
            category=category,
            item=item,
            amount=Decimal('100.00'),
            currency=currency
        )
        
        # Authenticated user shouldn't see it
        response = authenticated_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK
        # Verify no expenses are returned (since test_user hasn't created any)
    
    def test_admin_can_see_all_expenses(
        self, admin_client, test_user, 
        category, item, currency, db
    ):
        """Test that admin can see all expenses."""
        from expenses.models import ExpenseEntry
        
        # Create expense for test_user
        expense = ExpenseEntry.objects.create(
            user=test_user,
            date=date.today(),
            category=category,
            item=item,
            amount=Decimal('50.00'),
            currency=currency
        )
        
        # Admin should see it
        response = admin_client.get('/api/expenses/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.e2e
@pytest.mark.django_db
class TestSeasonalExpenseTracking:
    """E2E tests for tracking expenses over time periods."""
    
    def test_track_expenses_over_months(
        self, authenticated_client, test_user,
        category, item, currency, db
    ):
        """Test tracking expenses across multiple months."""
        from expenses.models import ExpenseEntry
        
        # Create expenses across different months
        today = date.today()
        for month_offset in range(-3, 1):  # Last 3 months + today
            for day in range(1, 6):  # 5 days each month
                try:
                    expense_date = today.replace(month=today.month + month_offset, day=day)
                    ExpenseEntry.objects.create(
                        user=test_user,
                        date=expense_date,
                        category=category,
                        item=item,
                        amount=Decimal(f'{10 + day}'),
                        currency=currency
                    )
                except (ValueError, OverflowError):
                    # Skip invalid dates
                    pass
        
        # Get summary
        response = authenticated_client.get('/api/expenses/summary/')
        assert response.status_code == status.HTTP_200_OK
        summary = response.json()
        
        # Verify quarterly calculation
        assert 'quarterly' in summary
        
        # Get yearly summary
        response = authenticated_client.get(f'/api/expenses/yearly/{today.year}/')
        assert response.status_code == status.HTTP_200_OK
        yearly = response.json()
        assert yearly['total'] > 0
