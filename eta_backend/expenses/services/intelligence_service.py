import re
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from ..models import Category, SubCategory, ExpenseEntry, Currency
from .currency_service import CurrencyService


CATEGORY_KEYWORDS = {
    'transport': ('transport', 'uber', 'taxi', 'fuel', 'petrol', 'bus', ' boda', 'motorcycle'),
    'food': ('food', 'lunch', 'dinner', 'breakfast', 'restaurant', 'groceries', 'grocery', 'market'),
    'utilities': ('electricity', 'water bill', 'internet', 'wifi', 'utility', 'utilities'),
    'housing': ('rent', 'house', 'housing'),
    'communication': ('airtime', 'phone', 'mobile', 'data bundle', 'communication'),
    'health': ('doctor', 'hospital', 'medicine', 'medical', 'health'),
    'school': ('school', 'tuition', 'fee', 'education'),
    'gift': ('gift', 'birthday', 'contribution', 'donation'),
}


class IntelligenceService:
    """Deterministic, explainable intelligence features for expense workflows."""

    @staticmethod
    def parse_quick_entry(text: str, user) -> dict:
        normalized = text.strip()
        amount_match = re.search(r'(?P<currency>USD|EUR|UGX|\$|€|USh)?\s*(?P<number>\d[\d,]*(?:\.\d+)?)\s*(?P<suffix>k|K)?', normalized)
        if not amount_match:
            return {'confidence': 0.0, 'errors': ['Enter an amount, for example: "I spent 35k at Java House for lunch".']}

        raw_number = Decimal(amount_match.group('number').replace(',', ''))
        if amount_match.group('suffix'):
            raw_number *= 1000
        currency_map = {'$': 'USD', '€': 'EUR', 'USh': 'UGX'}
        currency_code = currency_map.get(amount_match.group('currency'), amount_match.group('currency')) or 'EUR'
        if not Currency.objects.filter(code=currency_code, is_active=True).exists():
            currency_code = 'EUR'

        lowered = normalized.lower()
        parsed_date = date.today()
        if 'yesterday' in lowered:
            parsed_date -= timedelta(days=1)
        elif 'tomorrow' in lowered:
            parsed_date += timedelta(days=1)

        description = normalized
        at_match = re.search(r'\bat\s+(.+?)(?:\s+for\s+|\s+yesterday\b|\s+today\b|$)', normalized, re.IGNORECASE)
        if at_match:
            description = at_match.group(1).strip()
        elif 'for' in lowered:
            description = normalized.split('for', 1)[1].strip()
        description = re.sub(r'^(I\s+)?spent\s+', '', description, flags=re.IGNORECASE).strip(' .') or normalized

        category = IntelligenceService._suggest_category(lowered)
        subcategory = None
        if category:
            subcategory = SubCategory.objects.filter(category=category).order_by('name').first()

        return {
            'amount': str(raw_number.quantize(Decimal('0.01'))),
            'currency': currency_code,
            'date': parsed_date.isoformat(),
            'description': description,
            'category': category.id if category else None,
            'category_name': category.name if category else None,
            'subcategory': subcategory.id if subcategory else None,
            'subcategory_name': subcategory.name if subcategory else None,
            'confidence': 0.85 if category else 0.45,
            'needs_confirmation': True,
            'errors': [],
        }

    @staticmethod
    def _suggest_category(text: str):
        for category_name, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                category = Category.objects.filter(name__icontains=category_name, is_active=True).first()
                if category:
                    return category
        return Category.objects.filter(name__iexact='Other', is_active=True).first()

    @staticmethod
    def anomaly_summary(user, target_currency='EUR') -> list:
        expenses = list(ExpenseEntry.objects.filter(user=user).select_related('category', 'currency'))
        if len(expenses) < 3:
            return []
        grouped = {}
        for expense in expenses:
            value = float(CurrencyService.convert_amount(expense.amount * (expense.quantity or Decimal('1.00')), expense.currency.code, target_currency, expense.date) or 0)
            grouped.setdefault(expense.category_id, []).append((expense, value))
        results = []
        for entries in grouped.values():
            values = [value for _, value in entries]
            mean = sum(values) / len(values)
            variance = sum((value - mean) ** 2 for value in values) / len(values)
            std = variance ** 0.5
            threshold = mean + (2 * std)
            for expense, value in entries:
                if value > threshold and value > mean:
                    results.append({
                        'id': expense.id,
                        'category': expense.category.name,
                        'description': expense.item_description or expense.category.name,
                        'amount': value,
                        'message': f'{expense.category.name} spending of {value:.2f} is unusually high for this category.',
                    })
        return results

    @staticmethod
    def budget_recommendations(user, target_currency='EUR') -> list:
        totals = {}
        for expense in ExpenseEntry.objects.filter(user=user).select_related('category', 'currency'):
            value = float(CurrencyService.convert_amount(expense.amount * (expense.quantity or Decimal('1.00')), expense.currency.code, target_currency, expense.date) or 0)
            totals[expense.category.name] = totals.get(expense.category.name, 0) + value
        income = float(user.monthly_income or 0)
        total_historical = sum(totals.values())
        trend_scale = (income / total_historical) if income > 0 and total_historical > 0 else 1.1
        return [{
            'category': category,
            'recommended': round(total * trend_scale, 2),
            'historical': round(total, 2),
            'income': round(income, 2),
            'basis': 'historical spending, category trends, and monthly income',
        } for category, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)]

    @staticmethod
    def financial_insights(user, target_currency='EUR') -> list:
        expenses = list(ExpenseEntry.objects.filter(user=user).select_related('category', 'currency'))
        if not expenses:
            return []
        totals = {}
        for expense in expenses:
            line_total = float(CurrencyService.convert_amount(expense.amount * (expense.quantity or Decimal('1.00')), expense.currency.code, target_currency, expense.date) or 0)
            totals[expense.category.name] = totals.get(expense.category.name, 0) + line_total
        insights = []
        largest = max(totals.items(), key=lambda item: item[1])
        insights.append({'title': 'Largest spending category', 'message': f'{largest[0]} is your largest spending category at {largest[1]:.2f}.'})
        weekend = sum(float(CurrencyService.convert_amount(expense.amount * (expense.quantity or Decimal('1.00')), expense.currency.code, target_currency, expense.date) or 0) for expense in expenses if expense.date.weekday() >= 5)
        if weekend:
            insights.append({'title': 'Weekend spending', 'message': f'You spent {weekend:.2f} on weekend expenses.'})
        return insights
