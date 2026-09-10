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
            line_total = expense.amount * (expense.quantity or Decimal('1.00'))
            converted = CurrencyService.convert_amount(
                line_total,
                expense.currency.code,
                target_currency,
                expense.date
            ) or Decimal('0.00')
            total += converted
        return total

    def _detail_rows(self, queryset, target_currency: str = 'EUR') -> list:
        rows = []
        for number, expense in enumerate(queryset.select_related('category', 'subcategory', 'currency'), 1):
            line_total = expense.amount * (expense.quantity or Decimal('1.00'))
            converted_total = CurrencyService.convert_amount(
                line_total, expense.currency.code, target_currency, expense.date
            ) or Decimal('0.00')
            rows.append({
                'number': number,
                'date': expense.date.isoformat(),
                'description': expense.item_description or (expense.item.description if expense.item else expense.category.name),
                'category': expense.category.name,
                'subcategory': expense.subcategory.name if expense.subcategory else '',
                'amount': Decimal(expense.amount),
                'currency': expense.currency.code,
                'amount_eur': line_total if expense.currency.code == 'EUR' else CurrencyService.convert_amount(line_total, expense.currency.code, 'EUR', expense.date) or Decimal('0.00'),
                'amount_usd': CurrencyService.convert_amount(line_total, expense.currency.code, 'USD', expense.date) or Decimal('0.00'),
                'amount_ugx': line_total if expense.currency.code == 'UGX' else CurrencyService.convert_amount(line_total, expense.currency.code, 'UGX', expense.date) or Decimal('0.00'),
                'measurement': expense.measurement,
                'quantity': Decimal(expense.quantity or '1.00'),
                'total_amount': line_total,
                'total_converted': converted_total,
                'supplier': expense.supplier,
                'country': expense.country,
            })
        return rows

    def _export_rows_csv(self, title: str, period: str, queryset, target_currency: str) -> bytes:
        rows = self._detail_rows(queryset, target_currency)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([title, self.user.username, period])
        writer.writerow([])
        writer.writerow(['No', 'Date', 'Description', 'Category', 'Subcategory', 'Amount', 'Currency EUR', 'Currency USD', 'Currency UGX', 'Measurement', 'Quantity', 'Total Amount', 'Supplier', 'Country', f'Total in {target_currency}'])
        for row in rows:
            writer.writerow([
                row['number'], row['date'], row['description'], row['category'], row['subcategory'],
                f"{row['amount']:.2f}", f"{row['amount_eur']:.2f}", f"{row['amount_usd']:.2f}", f"{row['amount_ugx']:.2f}",
                row['measurement'], f"{row['quantity']:.2f}", f"{row['total_amount']:.2f}", row['supplier'], row['country'], f"{row['total_converted']:.2f}",
            ])
        writer.writerow([])
        writer.writerow(['Total', '', '', '', '', '', '', '', '', '', '', '', '', '', f"{sum((row['total_converted'] for row in rows), Decimal('0.00')):.2f} {target_currency}"])
        return output.getvalue().encode('utf-8')

    def _export_rows_pdf(self, title: str, period: str, queryset, target_currency: str) -> bytes:
        rows = self._detail_rows(queryset, target_currency)
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=10)
        headers = ['No', 'Date', 'Description', 'Amount', 'Currency', 'Measurement', 'Quantity', 'Total Amount', 'Supplier', 'Country']
        widths = [8, 22, 52, 18, 16, 20, 16, 24, 42, 35]

        def add_header():
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 7, f'{title} - {self.user.username}', 0, 1, 'C')
            pdf.set_font('Arial', '', 9)
            pdf.cell(0, 6, period, 0, 1, 'C')
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 7)
            for header, width in zip(headers, widths):
                pdf.cell(width, 6, header, 1, 0, 'C')
            pdf.ln()

        pdf.add_page()
        add_header()
        for row in rows:
            if pdf.get_y() > 185:
                pdf.add_page()
                add_header()
            values = [row['number'], row['date'], row['description'][:38], f"{row['amount']:.2f}", row['currency'], row['measurement'], f"{row['quantity']:.2f}", f"{row['total_amount']:.2f}", row['supplier'][:25], row['country'][:20]]
            pdf.set_font('Arial', '', 7)
            for index, (value, width) in enumerate(zip(values, widths)):
                if index == 4 and value == row['currency']:
                    pdf.set_font('Arial', 'B', 7)
                pdf.cell(width, 5, str(value), 1, 0, 'L' if index in (2, 8, 9) else 'C')
                pdf.set_font('Arial', '', 7)
            pdf.ln()
        pdf.set_font('Arial', 'B', 8)
        total = sum((row['total_converted'] for row in rows), Decimal('0.00'))
        pdf.cell(0, 7, f'Total: {total:.2f} {target_currency}', 0, 1, 'R')
        return bytes(pdf.output(dest='S'))
    
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

    def generate_custom_date_report(self, start_date: date, end_date: date, target_currency: str = 'EUR') -> dict:
        """Generate an expense report for a custom date range."""
        queryset = self._get_user_expenses().filter(date__gte=start_date, date__lte=end_date)
        total = self._convert_total(queryset, target_currency)

        breakdown = {}
        for expense in queryset.select_related('currency'):
            converted_amount = CurrencyService.convert_amount(
                expense.amount,
                expense.currency.code,
                target_currency,
                expense.date,
            ) or Decimal('0.00')
            key = expense.date.isoformat()
            breakdown[key] = breakdown.get(key, Decimal('0.00')) + converted_amount

        return {
            'period': 'custom_dates',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total': float(total),
            'target_currency': target_currency,
            'expense_count': queryset.count(),
            'average_expense': float(total / queryset.count()) if queryset.count() > 0 else 0,
            'daily_breakdown': {day: float(amount) for day, amount in sorted(breakdown.items())},
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

    def export_custom_date_report_csv(self, start_date: date, end_date: date, target_currency: str = 'EUR') -> bytes:
        queryset = self._get_user_expenses().filter(date__gte=start_date, date__lte=end_date)
        return self._export_rows_csv('Expense Tracker Custom Date Report', f'{start_date} to {end_date}', queryset, target_currency)
        report = self.generate_custom_date_report(start_date, end_date, target_currency)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Expense Tracker Custom Date Report'])
        writer.writerow(['Start Date', 'End Date', 'Currency', 'Total', 'Expense Count', 'Average Expense'])
        writer.writerow([
            report['start_date'],
            report['end_date'],
            report['target_currency'],
            report['total'],
            report['expense_count'],
            report['average_expense'],
        ])
        writer.writerow([])
        writer.writerow(['Date', 'Total'])
        for expense_date, total in report['daily_breakdown'].items():
            writer.writerow([expense_date, total])
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
        return bytes(pdf.output(dest='S'))

    def export_custom_date_report_pdf(self, start_date: date, end_date: date, target_currency: str = 'EUR') -> bytes:
        queryset = self._get_user_expenses().filter(date__gte=start_date, date__lte=end_date)
        return self._export_rows_pdf('Expense Tracker Custom Date Report', f'{start_date} to {end_date}', queryset, target_currency)
        report = self.generate_custom_date_report(start_date, end_date, target_currency)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Expense Tracker Custom Date Range Report', 0, 1, 'C')
        pdf.ln(5)
        pdf.set_font('Arial', '', 12)
        pdf.multi_cell(
            0,
            8,
            f"Start Date: {report['start_date']}\nEnd Date: {report['end_date']}\nCurrency: {report['target_currency']}\nTotal: {report['total']}\nExpense Count: {report['expense_count']}\nAverage Expense: {report['average_expense']}"
        )
        pdf.ln(5)
        pdf.cell(0, 8, 'Daily Breakdown', 0, 1)
        for expense_date, total in report['daily_breakdown'].items():
            pdf.cell(0, 8, f"{expense_date}: {total}", 0, 1)
        return bytes(pdf.output(dest='S'))

    def generate_category_report(self, year: int, month: int = None, target_currency: str = 'EUR') -> dict:
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
        
        categories = {}
        for expense in queryset.select_related('category', 'currency'):
            converted_amount = CurrencyService.convert_amount(
                expense.amount,
                expense.currency.code,
                target_currency,
                expense.date,
            ) or Decimal('0.00')
            category = categories.setdefault(expense.category.name, {
                'total': Decimal('0.00'),
                'percentage': 0
            })
            category['total'] += converted_amount

        categories = dict(sorted(categories.items(), key=lambda item: item[1]['total'], reverse=True))
        
        total = sum((cat['total'] for cat in categories.values()), Decimal('0.00'))
        
        # Calculate percentages
        for category in categories.values():
            if total > 0:
                category['percentage'] = round((category['total'] / total) * 100, 2)
            category['total'] = float(category['total'])
        
        return {
            'period': 'monthly' if month else 'yearly',
            'year': year,
            'month': month,
            'total': float(total),
            'target_currency': target_currency,
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
        queryset = self._get_user_expenses().filter(date__year=year, date__month=month)
        return self._export_rows_csv('Expense Tracker Monthly Report', f'{month:02d}/{year}', queryset, target_currency)
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
        queryset = self._get_user_expenses().filter(date__year=year)
        return self._export_rows_csv('Expense Tracker Yearly Report', str(year), queryset, target_currency)
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
        queryset = self._get_user_expenses().filter(date__year=year, date__month=month)
        return self._export_rows_pdf('Expense Tracker Monthly Report', f'{month:02d}/{year}', queryset, target_currency)
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
        queryset = self._get_user_expenses().filter(date__year=year)
        return self._export_rows_pdf('Expense Tracker Yearly Report', str(year), queryset, target_currency)
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
        queryset = self._get_user_expenses().filter(date__year__gte=start_year, date__year__lte=end_year)
        return self._export_rows_csv('Expense Tracker Year Range Report', f'{start_year} to {end_year}', queryset, target_currency)
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
        queryset = self._get_user_expenses().filter(date__year__gte=start_year, date__year__lte=end_year)
        return self._export_rows_pdf('Expense Tracker Year Range Report', f'{start_year} to {end_year}', queryset, target_currency)
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
