"""
Service layer tests - Business logic tests.
These tests focus on the service layer and business logic.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from expenses.services.expense_service import ExpenseService
from expenses.services.summary_service import SummaryService
from expenses.services.currency_service import CurrencyService
from expenses.services.report_service import ReportService


@pytest.mark.unit
@pytest.mark.django_db
class TestExpenseService:
    """Test the ExpenseService business logic."""
    
    def test_create_expense(self, test_user, category, item, currency):
        """Test creating an expense through the service."""
        service = ExpenseService(test_user)
        expense_data = {
            'date': date.today(),
            'category': category,
            'item': item,
            'amount': Decimal('50.00'),
            'currency': currency,
        }
        expense = service.create_expense(expense_data)
        
        assert expense.id is not None
        assert expense.user == test_user
        assert expense.amount == Decimal('50.00')
    
    def test_get_user_expenses(self, test_user, multiple_expenses):
        """Test retrieving user's expenses."""
        service = ExpenseService(test_user)
        expenses = service.get_user_expenses()
        
        assert expenses.count() == 10
        assert all(e.user == test_user for e in expenses)
    
    def test_get_expenses_by_date_range(self, test_user, multiple_expenses):
        """Test filtering expenses by date range."""
        service = ExpenseService(test_user)
        today = date.today()
        three_days_ago = today - timedelta(days=3)
        
        expenses = service.get_expenses_by_date_range(three_days_ago, today)
        
        # Should include expenses from today back 3 days
        assert expenses.count() > 0
        assert all(three_days_ago <= e.date <= today for e in expenses)
    
    def test_get_total_expenses(self, test_user, multiple_expenses):
        """Test calculating total expenses."""
        service = ExpenseService(test_user)
        total = service.get_total_expenses()
        
        # multiple_expenses creates expenses with amounts 10, 12, 14, 16, 18, 20, 22, 24, 26, 28
        expected_total = sum(10 + i * 2 for i in range(10))
        assert total == Decimal(str(expected_total))
    
    def test_get_expenses_by_category(self, test_user, multiple_expenses):
        """Test getting expenses grouped by category."""
        service = ExpenseService(test_user)
        by_category = service.get_expenses_by_category()
        
        assert isinstance(by_category, dict)
        assert len(by_category) > 0
    
    def test_get_top_expensive_categories(self, test_user, multiple_expenses):
        """Test getting top expensive categories."""
        service = ExpenseService(test_user)
        top = service.get_top_expensive_categories(limit=5)
        
        assert isinstance(top, list)
        assert len(top) <= 5
        # Should be ordered by total descending
        if len(top) > 1:
            assert top[0]['total'] >= top[1]['total']
    
    def test_get_least_expensive_categories(self, test_user, multiple_expenses):
        """Test getting least expensive categories."""
        service = ExpenseService(test_user)
        least = service.get_least_expensive_categories(limit=3)
        
        assert isinstance(least, list)
        assert len(least) <= 3
    
    def test_update_expense(self, test_user, expense_entry):
        """Test updating an expense."""
        service = ExpenseService(test_user)
        updated_expense = service.update_expense(
            expense_entry.id,
            {'amount': Decimal('100.00')}
        )
        
        assert updated_expense.amount == Decimal('100.00')
    
    def test_delete_expense(self, test_user, expense_entry):
        """Test deleting an expense."""
        service = ExpenseService(test_user)
        result = service.delete_expense(expense_entry.id)
        
        assert result is True
        from expenses.models import ExpenseEntry
        assert not ExpenseEntry.objects.filter(id=expense_entry.id).exists()


@pytest.mark.unit
@pytest.mark.django_db
class TestSummaryService:
    """Test the SummaryService business logic."""
    
    def test_get_daily_summary_today(self, test_user, multiple_expenses):
        """Test getting today's expense summary."""
        service = SummaryService(test_user)
        today_total = service.get_daily_summary()
        
        # At least one expense should be today
        assert today_total >= 0
    
    def test_get_daily_summary_specific_date(self, test_user, multiple_expenses):
        """Test getting summary for a specific date."""
        service = SummaryService(test_user)
        specific_date = date.today() - timedelta(days=2)
        total = service.get_daily_summary(specific_date)
        
        assert isinstance(total, Decimal)
        assert total >= 0
    
    def test_get_weekly_summary(self, test_user, multiple_expenses):
        """Test getting weekly summary."""
        service = SummaryService(test_user)
        weekly_total = service.get_weekly_summary()
        
        assert isinstance(weekly_total, Decimal)
        assert weekly_total > 0
    
    def test_get_monthly_summary(self, test_user, multiple_expenses):
        """Test getting monthly summary."""
        service = SummaryService(test_user)
        monthly_total = service.get_monthly_summary()
        
        assert isinstance(monthly_total, Decimal)
        assert monthly_total > 0
    
    def test_get_quarterly_summary(self, test_user, multiple_expenses):
        """Test getting quarterly summary."""
        service = SummaryService(test_user)
        quarterly_total = service.get_quarterly_summary()
        
        assert isinstance(quarterly_total, Decimal)
        assert quarterly_total > 0
    
    def test_get_annual_summary(self, test_user, multiple_expenses):
        """Test getting annual summary."""
        service = SummaryService(test_user)
        annual_total = service.get_annual_summary()
        
        assert isinstance(annual_total, Decimal)
        assert annual_total > 0
    
    def test_get_all_summaries(self, test_user, multiple_expenses):
        """Test getting all summaries at once."""
        service = SummaryService(test_user)
        all_summaries = service.get_all_summaries()
        
        assert 'daily' in all_summaries
        assert 'weekly' in all_summaries
        assert 'monthly' in all_summaries
        assert 'quarterly' in all_summaries
        assert 'annual' in all_summaries
        
        # Larger periods should have more or equal expenses
        assert all_summaries['annual'] >= all_summaries['quarterly']
        assert all_summaries['quarterly'] >= all_summaries['monthly']
        assert all_summaries['monthly'] >= all_summaries['weekly']
    
    def test_get_yearly_total(self, test_user, multiple_expenses):
        """Test getting total for a specific year."""
        service = SummaryService(test_user)
        year = date.today().year
        total = service.get_yearly_total(year)
        
        assert isinstance(total, Decimal)
        assert total > 0
    
    def test_get_yearly_by_month(self, test_user, multiple_expenses):
        """Test getting monthly breakdown for a year."""
        service = SummaryService(test_user)
        year = date.today().year
        monthly_breakdown = service.get_yearly_by_month(year)
        
        assert isinstance(monthly_breakdown, dict)


@pytest.mark.unit
class TestCurrencyService:
    """Test the CurrencyService business logic."""
    
    def test_get_latest_rate_same_currency(self):
        """Test getting rate for same currency returns 1."""
        rate = CurrencyService.get_latest_rate('EUR', 'EUR')
        assert rate == 1.0
    
    @pytest.mark.django_db
    def test_get_latest_rate_from_database(self, currency_rate):
        """Test getting rate from database."""
        rate = CurrencyService.get_latest_rate('EUR', 'USD')
        assert rate == 1.1
    
    @pytest.mark.django_db
    def test_convert_amount(self, currency_rate):
        """Test converting amount between currencies."""
        amount = Decimal('100')
        converted = CurrencyService.convert_amount(amount, 'EUR', 'USD')
        
        assert converted == Decimal('110')
    
    @pytest.mark.django_db
    def test_convert_amount_invalid_input(self, currency_rate):
        """Test converting with invalid input."""
        converted = CurrencyService.convert_amount('invalid', 'EUR', 'USD')
        assert converted is None
    
    @pytest.mark.django_db
    def test_save_rate(self, currency, usd_currency):
        """Test saving a new exchange rate."""
        from expenses.models import CurrencyRate
        
        rate_obj = CurrencyService.save_rate('EUR', 'USD', Decimal('1.15'))
        
        assert rate_obj is not None
        assert rate_obj.rate == Decimal('1.15')
        assert CurrencyRate.objects.filter(
            base_currency__code='EUR',
            target_currency__code='USD'
        ).exists()
    
    @pytest.mark.django_db
    def test_get_rate_history(self, currency_rate):
        """Test getting historical rates."""
        history = CurrencyService.get_rate_history('EUR', 'USD', limit=10)
        
        assert isinstance(history, list)


@pytest.mark.unit
@pytest.mark.django_db
class TestReportService:
    """Test the ReportService business logic."""
    
    def test_generate_monthly_report(self, test_user, multiple_expenses):
        """Test generating a monthly report."""
        service = ReportService(test_user)
        today = date.today()
        report = service.generate_monthly_report(today.year, today.month)
        
        assert report['period'] == 'monthly'
        assert report['year'] == today.year
        assert report['month'] == today.month
        assert report['total'] > 0
        assert 'expense_count' in report
        assert 'average_expense' in report
    
    def test_generate_yearly_report(self, test_user, multiple_expenses):
        """Test generating a yearly report."""
        service = ReportService(test_user)
        year = date.today().year
        report = service.generate_yearly_report(year)
        
        assert report['period'] == 'yearly'
        assert report['year'] == year
        assert report['total'] > 0
        assert 'monthly_breakdown' in report

    def test_generate_year_range_report(self, test_user, multiple_expenses):
        """Test generating a year range report."""
        service = ReportService(test_user)
        today = date.today()
        report = service.generate_year_range_report(today.year - 1, today.year)

        assert report['period'] == 'year_range'
        assert report['start_year'] == today.year - 1
        assert report['end_year'] == today.year
        assert 'yearly_breakdown' in report

    def test_export_yearly_report_csv(self, test_user, multiple_expenses):
        """Test exporting yearly report as CSV."""
        service = ReportService(test_user)
        today = date.today()
        csv_bytes = service.export_yearly_report_csv(today.year)
        assert isinstance(csv_bytes, bytes)
        assert b'Expense Tracker Yearly Report' in csv_bytes

    def test_export_yearly_report_pdf(self, test_user, multiple_expenses):
        """Test exporting yearly report as PDF."""
        service = ReportService(test_user)
        today = date.today()
        pdf_bytes = service.export_yearly_report_pdf(today.year)
        assert isinstance(pdf_bytes, bytes)
        assert b'%PDF' in pdf_bytes
    
    def test_generate_category_report(self, test_user, multiple_expenses):
        """Test generating category breakdown report."""
        service = ReportService(test_user)
        today = date.today()
        report = service.generate_category_report(today.year, today.month)
        
        assert 'categories' in report
        assert isinstance(report['categories'], dict)
        # Each category should have total and percentage
        for cat in report['categories'].values():
            assert 'total' in cat
            assert 'percentage' in cat
            assert 0 <= cat['percentage'] <= 100
    
    def test_generate_comparison_report(self, test_user, multiple_expenses):
        """Test generating comparison between two periods."""
        service = ReportService(test_user)
        today = date.today()
        
        # Compare this month with last month
        report = service.generate_comparison_report(
            today.year,
            today.month - 1 or 12,
            today.year if today.month > 1 else today.year - 1,
            today.month
        )
        
        assert 'period1' in report
        assert 'period2' in report
        assert 'difference' in report
        assert 'percentage_change' in report
        assert 'trend' in report
        assert report['trend'] in ['up', 'down', 'stable']
