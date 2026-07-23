"""
Report Service - Business logic for generating and exporting reports.
Separates report generation from view layer.
"""
import csv
from io import BytesIO, StringIO
from datetime import date
from decimal import Decimal
from fpdf import FPDF
from ..models import ExpenseEntry
from .currency_service import CurrencyService
from django.db.models import Sum
from accounts.models import User


class ReportService:
    """Service for report generation and exports."""
    
    def __init__(self, user: User):
        self.user = user
    
    def _get_user_expenses(self):
        """Get all expenses for the user."""
        return ExpenseEntry.objects.filter(user=self.user)
    
    def _convert_total(self, queryset, target_currency: str = 'EUR') -> Decimal:
        total = Decimal('0.00')
        for expense in queryset.select_related('currency'):
            converted = CurrencyService.convert_amount(
                expense.amount,
                expense.currency.code,
                target_currency,
                expense.date
            ) or Decimal('0.00')
            total += converted
        return total
    
    def generate_monthly_report(self, year: int, month: int, 
                               target_currency: str = 'EUR') -> dict:
        """
        Generate a monthly expense report.
        
        Args:
            year: Report year
            month: Report month
            target_currency: Currency for conversion
            
        Returns:
            Dictionary with report data
        """
        queryset = self._get_user_expenses().filter(
            date__year=year,
            date__month=month
        )
        
        total = self._convert_total(queryset, target_currency)
        
        return {
            'period': 'monthly',
            'year': year,
            'month': month,
            'total': float(total),
            'target_currency': target_currency,
            'converted_total': float(total) if target_currency else None,
            'expense_count': queryset.count(),
            'average_expense': float(total / queryset.count()) if queryset.count() > 0 else 0
        }
    
    def generate_yearly_report(self, year: int, 
                              target_currency: str = 'EUR') -> dict:
        """
        Generate a yearly expense report.
        
        Args:
            year: Report year
            target_currency: Currency for conversion
            
        Returns:
            Dictionary with report data
        """
        queryset = self._get_user_expenses().filter(date__year=year)
        
        total = self._convert_total(queryset, target_currency)
        
        # Get monthly breakdown by converting each expense
        monthly_totals = {}
        for expense in queryset.select_related('currency'):
            converted_amount = CurrencyService.convert_amount(
                expense.amount,
                expense.currency.code,
                target_currency,
                expense.date
            ) or Decimal('0.00')
            month = expense.date.month
            monthly_totals[month] = monthly_totals.get(month, Decimal('0.00')) + converted_amount

        monthly_breakdown = {month: float(total) for month, total in sorted(monthly_totals.items())}
        
        return {
            'period': 'yearly',
            'year': year,
            'total': float(total),
            'target_currency': target_currency,
            'converted_total': float(total) if target_currency else None,
            'expense_count': queryset.count(),
            'average_expense': float(total / queryset.count()) if queryset.count() > 0 else 0,
            'monthly_breakdown': monthly_breakdown
        }

    def generate_year_range_report(self, start_year: int, end_year: int, target_currency: str = 'EUR') -> dict:
        """
        Generate a report covering a range of years.
        """
        queryset = self._get_user_expenses().filter(date__year__gte=start_year, date__year__lte=end_year)
        total = self._convert_total(queryset, target_currency)

        yearly_breakdown = {}
        for expense in queryset.select_related('currency'):
            converted_amount = CurrencyService.convert_amount(
                expense.amount,
                expense.currency.code,
                target_currency,
                expense.date
            ) or Decimal('0.00')
            year = expense.date.year
            yearly_breakdown[year] = yearly_breakdown.get(year, Decimal('0.00')) + converted_amount

        return {
            'period': 'year_range',
            'start_year': start_year,
            'end_year': end_year,
            'total': float(total),
            'target_currency': target_currency,
            'expense_count': queryset.count(),
            'average_expense': float(total / queryset.count()) if queryset.count() > 0 else 0,
            'yearly_breakdown': {year: float(total) for year, total in sorted(yearly_breakdown.items())}
        }

    def export_year_range_report_csv(self, start_year: int, end_year: int, target_currency: str = 'EUR') -> bytes:
        report = self.generate_year_range_report(start_year, end_year, target_currency)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Expense Tracker Year Range Report'])
        writer.writerow(['Start Year', 'End Year', 'Currency', 'Total', 'Expense Count', 'Average Expense'])
        writer.writerow([
            report['start_year'],
            report['end_year'],
            report['target_currency'],
            report['total'],
            report['expense_count'],
            report['average_expense'],
        ])
        writer.writerow([])
        writer.writerow(['Year', 'Total'])
        for year, total in report['yearly_breakdown'].items():
            writer.writerow([year, total])
        return output.getvalue().encode('utf-8')

    def export_year_range_report_pdf(self, start_year: int, end_year: int, target_currency: str = 'EUR') -> bytes:
        report = self.generate_year_range_report(start_year, end_year, target_currency)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Expense Tracker Year Range Report', 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(
            0,
            8,
            f"Start Year: {report['start_year']}\nEnd Year: {report['end_year']}\nCurrency: {report['target_currency']}\nTotal: {report['total']}\nExpense Count: {report['expense_count']}\nAverage Expense: {report['average_expense']}"
        )
        pdf.ln(5)
        pdf.cell(0, 8, 'Yearly Breakdown', 0, 1)
        for year, total in report['yearly_breakdown'].items():
            pdf.cell(0, 8, f"{year}: {total}", 0, 1)
        return pdf.output(dest='S').encode('latin-1')

    def generate_category_report(self, year: int, month: int = None) -> dict:
        """
        Generate expense report by category.
        
        Args:
            year: Report year
            month: Report month (optional)
            
        Returns:
            Dictionary with category breakdown
        """
        queryset = self._get_user_expenses().filter(date__year=year)
        
        if month is not None:
            queryset = queryset.filter(date__month=month)
        
        category_data = queryset.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        categories = {
            item['category__name']: {
                'total': float(item['total']),
                'percentage': 0
            }
            for item in category_data
        }
        
        total = sum(cat['total'] for cat in categories.values())
        
        # Calculate percentages
        for category in categories.values():
            if total > 0:
                category['percentage'] = round((category['total'] / total) * 100, 2)
        
        return {
            'period': 'monthly' if month else 'yearly',
            'year': year,
            'month': month,
            'total': float(total),
            'categories': categories
        }
    
    def generate_comparison_report(self, year1: int, month1: int, 
                                   year2: int, month2: int) -> dict:
        """
        Generate comparison report between two periods.
        
        Args:
            year1: First period year
            month1: First period month
            year2: Second period year
            month2: Second period month
            
        Returns:
            Dictionary with comparison data
        """
        period1 = self._get_user_expenses().filter(
            date__year=year1,
            date__month=month1
        )
        period2 = self._get_user_expenses().filter(
            date__year=year2,
            date__month=month2
        )
        
        total1 = period1.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        total2 = period2.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Calculate difference
        diff = total2 - total1
        percentage_change = 0
        if total1 > 0:
            percentage_change = float((diff / total1) * 100)
        
        return {
            'period1': f'{year1}-{month1:02d}',
            'period1_total': float(total1),
            'period2': f'{year2}-{month2:02d}',
            'period2_total': float(total2),
            'difference': float(diff),
            'percentage_change': percentage_change,
            'trend': 'up' if diff > 0 else 'down' if diff < 0 else 'stable'
        }

    def export_monthly_report_csv(self, year: int, month: int, target_currency: str = 'EUR') -> bytes:
        report = self.generate_monthly_report(year, month, target_currency)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Expense Tracker Monthly Report'])
        writer.writerow(['Year', 'Month', 'Currency', 'Total', 'Expense Count', 'Average Expense'])
        writer.writerow([
            report['year'],
            report['month'],
            report['target_currency'],
            report['total'],
            report['expense_count'],
            report['average_expense'],
        ])
        writer.writerow([])
        writer.writerow(['Notes'])
        writer.writerow([f"Generated report for {report['month']}/{report['year']} in {report['target_currency']}"])
        return output.getvalue().encode('utf-8')

    def export_yearly_report_csv(self, year: int, target_currency: str = 'EUR') -> bytes:
        report = self.generate_yearly_report(year, target_currency)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Expense Tracker Yearly Report'])
        writer.writerow(['Year', 'Currency', 'Total', 'Expense Count', 'Average Expense'])
        writer.writerow([
            report['year'],
            report['target_currency'],
            report['total'],
            report['expense_count'],
            report['average_expense'],
        ])
        writer.writerow([])
        writer.writerow(['Monthly Breakdown'])
        writer.writerow(['Month', 'Total'])
        for month, total in report['monthly_breakdown'].items():
            writer.writerow([month, total])
        return output.getvalue().encode('utf-8')

    def export_monthly_report_pdf(self, year: int, month: int, target_currency: str = 'EUR') -> bytes:
        report = self.generate_monthly_report(year, month, target_currency)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Expense Tracker Monthly Report', 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(0, 8, f"Year: {report['year']}\nMonth: {report['month']}\nCurrency: {report['target_currency']}\nTotal: {report['total']}\nExpense Count: {report['expense_count']}\nAverage Expense: {report['average_expense']}")
        return bytes(pdf.output(dest='S'))

    def export_yearly_report_pdf(self, year: int, target_currency: str = 'EUR') -> bytes:
        report = self.generate_yearly_report(year, target_currency)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Expense Tracker Yearly Report', 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(
            0,
            8,
            f"Year: {report['year']}\nCurrency: {report['target_currency']}\nTotal: {report['total']}\nExpense Count: {report['expense_count']}\nAverage Expense: {report['average_expense']}"
        )
        pdf.ln(5)
        pdf.cell(0, 8, 'Monthly Breakdown', 0, 1)
        for month, total in report['monthly_breakdown'].items():
            pdf.cell(0, 8, f"Month {month}: {total}", 0, 1)
        return bytes(pdf.output(dest='S'))
    
    def export_year_range_report_csv(self, start_year: int, end_year: int, target_currency: str = 'EUR') -> bytes:
        """Export year range report as CSV."""
        report = self.generate_year_range_report(start_year, end_year, target_currency)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Expense Tracker Year Range Report'])
        writer.writerow(['Period', 'Currency', 'Total', 'Expense Count', 'Average Expense'])
        writer.writerow([
            f"{start_year}-{end_year}",
            report['target_currency'],
            report['total'],
            report['expense_count'],
            report['average_expense'],
        ])
        writer.writerow([])
        writer.writerow(['Yearly Breakdown'])
        writer.writerow(['Year', 'Total'])
        for year, yearly_data in report['yearly_breakdown'].items():
            writer.writerow([year, yearly_data['total']])
        return output.getvalue().encode('utf-8')
    
    def export_year_range_report_pdf(self, start_year: int, end_year: int, target_currency: str = 'EUR') -> bytes:
        """Export year range report as PDF."""
        report = self.generate_year_range_report(start_year, end_year, target_currency)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'Expense Tracker Report {start_year}-{end_year}', 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(
            0,
            8,
            f"Period: {start_year}-{end_year}\nCurrency: {report['target_currency']}\nTotal: {report['total']}\nExpense Count: {report['expense_count']}\nAverage Expense: {report['average_expense']}"
        )
        pdf.ln(5)
        pdf.cell(0, 8, 'Yearly Breakdown', 0, 1)
        for year, yearly_data in report['yearly_breakdown'].items():
            pdf.cell(0, 8, f"Year {year}: {yearly_data['total']}", 0, 1)
        return bytes(pdf.output(dest='S'))
