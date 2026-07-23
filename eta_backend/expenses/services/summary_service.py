"""
Summary Service - Business logic for expense summaries and reports.
Separates calculation logic from view layer.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum, QuerySet
from accounts.models import User
from .currency_service import CurrencyService
from ..models import ExpenseEntry


class SummaryService:
    """Service for summary and reporting business logic."""
    
    def __init__(self, user: User):
        self.user = user
    
    def _get_user_expenses(self) -> QuerySet:
        """Get all expenses for the user."""
        return ExpenseEntry.objects.filter(user=self.user)
    
    def _calculate_total(self, queryset: QuerySet, target_currency: str = 'EUR') -> Decimal:
        """Calculate total from a queryset with currency conversion."""
        total = Decimal('0.00')
        for expense in queryset.select_related('currency'):
            converted_amount = CurrencyService.convert_amount(
                expense.amount,
                expense.currency.code,
                target_currency,
                expense.date
            )
            total += converted_amount or Decimal('0.00')
        return total
    
    def get_daily_summary(self, target_date: date = None, target_currency: str = 'EUR') -> Decimal:
        """
        Get total expenses for a specific day.
        
        Args:
            target_date: Date to summarize. Defaults to today.
            
        Returns:
            Total expenses for that day
        """
        if target_date is None:
            target_date = date.today()
        
        queryset = self._get_user_expenses().filter(date=target_date)
        return self._calculate_total(queryset, target_currency)
    
    def get_weekly_summary(self, target_date: date = None, target_currency: str = 'EUR') -> Decimal:
        """
        Get total expenses for the current week.
        
        Args:
            target_date: Reference date. Defaults to today.
            
        Returns:
            Total expenses for that week
        """
        if target_date is None:
            target_date = date.today()
        
        week_ago = target_date - timedelta(days=7)
        queryset = self._get_user_expenses().filter(
            date__gte=week_ago,
            date__lte=target_date
        )
        return self._calculate_total(queryset, target_currency)
    
    def get_monthly_summary(self, target_date: date = None, target_currency: str = 'EUR') -> Decimal:
        """
        Get total expenses for the current month.
        
        Args:
            target_date: Reference date. Defaults to today.
            
        Returns:
            Total expenses for that month
        """
        if target_date is None:
            target_date = date.today()
        
        start_month = target_date.replace(day=1)
        queryset = self._get_user_expenses().filter(
            date__gte=start_month,
            date__lte=target_date
        )
        return self._calculate_total(queryset, target_currency)
    
    def get_quarterly_summary(self, target_date: date = None, target_currency: str = 'EUR') -> Decimal:
        """
        Get total expenses for the current quarter.
        
        Args:
            target_date: Reference date. Defaults to today.
            
        Returns:
            Total expenses for that quarter
        """
        if target_date is None:
            target_date = date.today()
        
        quarter_start = target_date.replace(
            month=((target_date.month - 1) // 3) * 3 + 1, 
            day=1
        )
        queryset = self._get_user_expenses().filter(
            date__gte=quarter_start,
            date__lte=target_date
        )
        return self._calculate_total(queryset, target_currency)
    
    def get_annual_summary(self, target_date: date = None, target_currency: str = 'EUR') -> Decimal:
        """
        Get total expenses for the current year.
        
        Args:
            target_date: Reference date. Defaults to today.
            
        Returns:
            Total expenses for that year
        """
        if target_date is None:
            target_date = date.today()
        
        start_year = target_date.replace(month=1, day=1)
        queryset = self._get_user_expenses().filter(
            date__gte=start_year,
            date__lte=target_date
        )
        return self._calculate_total(queryset, target_currency)
    
    def get_all_summaries(self, target_date: date = None, target_currency: str = 'EUR') -> dict:
        """
        Get all time-period summaries at once.
        
        Args:
            target_date: Reference date. Defaults to today.
            
        Returns:
            Dictionary with daily, weekly, monthly, quarterly, annual totals
        """
        if target_date is None:
            target_date = date.today()
        
        return {
            'daily': self.get_daily_summary(target_date, target_currency),
            'weekly': self.get_weekly_summary(target_date, target_currency),
            'monthly': self.get_monthly_summary(target_date, target_currency),
            'quarterly': self.get_quarterly_summary(target_date, target_currency),
            'annual': self.get_annual_summary(target_date, target_currency),
        }
    
    def get_yearly_total(self, year: int, target_currency: str = 'EUR') -> Decimal:
        """
        Get total expenses for a specific year.
        
        Args:
            year: Year to summarize
            
        Returns:
            Total expenses for that year
        """
        queryset = self._get_user_expenses().filter(date__year=year)
        return self._calculate_total(queryset, target_currency)
    
    def get_yearly_by_month(self, year: int, target_currency: str = 'EUR') -> dict:
        """
        Get monthly breakdown for a specific year.
        
        Args:
            year: Year to break down
            target_currency: Currency for conversion
            
        Returns:
            Dictionary with month numbers as keys and totals as values
        """
        monthly_totals = {}
        queryset = self._get_user_expenses().filter(date__year=year).select_related('currency')

        for expense in queryset:
            converted_amount = CurrencyService.convert_amount(
                expense.amount,
                expense.currency.code,
                target_currency,
                expense.date
            ) or Decimal('0.00')
            month = expense.date.month
            monthly_totals[month] = monthly_totals.get(month, Decimal('0.00')) + converted_amount

        return {month: total for month, total in sorted(monthly_totals.items())}
