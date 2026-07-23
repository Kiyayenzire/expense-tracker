"""
Expense Service - Business logic for expense operations.
Separates business logic from view layer.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum, QuerySet
from accounts.models import User
from ..models import ExpenseEntry, Category, Currency, CurrencyRate


class ExpenseService:
    """Service for expense-related business logic."""
    
    def __init__(self, user: User):
        self.user = user
    
    def create_expense(self, data: dict) -> ExpenseEntry:
        """
        Create a new expense entry for the user.
        
        Args:
            data: Dictionary containing expense data
            
        Returns:
            Created ExpenseEntry instance
        """
        data['user'] = self.user
        return ExpenseEntry.objects.create(**data)
    
    def get_user_expenses(self) -> QuerySet:
        """Get all expenses for the user."""
        return ExpenseEntry.objects.filter(user=self.user).select_related(
            'category', 'item', 'currency', 'subcategory'
        ).order_by('-date', '-created_at')
    
    def get_expenses_by_date_range(self, start_date: date, end_date: date) -> QuerySet:
        """Get expenses within a date range."""
        return self.get_user_expenses().filter(
            date__gte=start_date, 
            date__lte=end_date
        )
    
    def get_total_expenses(self) -> Decimal:
        """Get total amount spent by user."""
        total = self.get_user_expenses().aggregate(total=Sum('amount'))['total']
        return total or Decimal('0.00')
    
    def get_expenses_by_category(self) -> dict:
        """
        Get total expenses grouped by category.
        
        Returns:
            Dictionary with category names as keys and totals as values
        """
        expenses = self.get_user_expenses().values(
            'category__name'
        ).annotate(total=Sum('amount')).order_by('-total')
        
        return {
            item['category__name']: item['total'] 
            for item in expenses
        }
    
    def get_top_expensive_categories(self, limit: int = 5) -> list:
        """Get the most expensive categories."""
        return list(self.get_user_expenses().values(
            'category__name'
        ).annotate(total=Sum('amount')).order_by('-total')[:limit])
    
    def get_least_expensive_categories(self, limit: int = 3) -> list:
        """Get the least expensive categories."""
        return list(self.get_user_expenses().values(
            'category__name'
        ).annotate(total=Sum('amount')).order_by('total')[:limit])
    
    def update_expense(self, expense_id: int, data: dict) -> ExpenseEntry:
        """Update an existing expense entry."""
        expense = ExpenseEntry.objects.get(id=expense_id, user=self.user)
        for key, value in data.items():
            setattr(expense, key, value)
        expense.save()
        return expense
    
    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense entry."""
        expense = ExpenseEntry.objects.get(id=expense_id, user=self.user)
        expense.delete()
        return True
