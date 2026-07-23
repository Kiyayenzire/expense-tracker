from django.core.management.base import BaseCommand
from expenses.models import Category, SubCategory, Item, Currency, CurrencyRate
from decimal import Decimal
from datetime import date


class Command(BaseCommand):
    help = 'Seed initial categories, subcategories, items, currencies, and exchange rates.'

    def handle(self, *args, **options):
        categories = [
            ('Rent', '#10B981'),
            ('Water', '#3B82F6'),
            ('Electricity', '#8B5CF6'),
            ('Medical', '#EF4444'),
            ('Vegetables', '#F97316'),
            ('Proteins', '#F59E0B'),
            ('Carbohydrates', '#06B6D4'),
            ('Dairy products', '#64748B'),
            ('Fruits', '#10B981'),
            ('Gas', '#2563EB'),
            ('Books', '#EC4899'),
            ('Cinema', '#F59E0B'),
            ('Travel', '#3B82F6'),
            ('Gifts', '#EF4444'),
            ('Birthdays', '#F97316'),
            ('Parties', '#EC4899'),
            ('School', '#14B8A6'),
            ('School trips', '#0D9488'),
            ('Food', '#F97316'),
            ('Transport', '#3B82F6'),
            ('Utilities', '#8B5CF6'),
            ('Shopping', '#EC4899'),
            ('Healthcare', '#EF4444'),
            ('Entertainment', '#F59E0B'),
            ('Education', '#06B6D4'),
            ('Salary', '#10B981'),
            ('Investments', '#14B8A6'),
        ]

        created_categories = {}
        for name, color in categories:
            category, _ = Category.objects.get_or_create(name=name, defaults={'color': color, 'is_active': True})
            created_categories[name] = category

        proteins = created_categories.get('Proteins')
        if proteins:
            for name in ['Animal Proteins', 'Plant Proteins']:
                SubCategory.objects.get_or_create(name=name, category=proteins)

        items = [
            ('Monthly rent', 'Rent'),
            ('City water bill', 'Water'),
            ('Electric meter', 'Electricity'),
            ('Doctor visit', 'Medical'),
            ('Tomatoes batch', 'Vegetables'),
            ('Chicken breast', 'Proteins'),
            ('Beans', 'Proteins'),
            ('Pasta', 'Carbohydrates'),
            ('Milk pack', 'Dairy products'),
            ('Bananas', 'Fruits'),
            ('Cooking gas', 'Gas'),
            ('School books', 'Books'),
            ('Cinema tickets', 'Cinema'),
            ('Train fare', 'Travel'),
            ('Birthday gift', 'Gifts'),
            ('Party catering', 'Parties'),
            ('School fees', 'School'),
            ('Trip allowance', 'School trips'),
        ]

        for description, category_name in items:
            category = created_categories.get(category_name)
            if category:
                Item.objects.get_or_create(description=description, category=category)

        currencies = [
            ('EUR', 'Euro', '€'),
            ('USD', 'US Dollar', '$'),
            ('UGX', 'Ugandan Shilling', 'USh'),
        ]

        created_currencies = {}
        for code, name, symbol in currencies:
            currency, _ = Currency.objects.get_or_create(code=code, defaults={'name': name, 'symbol': symbol, 'is_active': True})
            created_currencies[code] = currency

        today = date.today()
        rates = [
            ('EUR', 'USD', Decimal('1.10')),
            ('EUR', 'UGX', Decimal('4100.00')),
            ('USD', 'UGX', Decimal('3727.27')),
            ('USD', 'EUR', Decimal('0.91')),
            ('UGX', 'EUR', Decimal('0.00024')),
            ('UGX', 'USD', Decimal('0.00027')),
        ]

        for base, target, rate in rates:
            base_currency = created_currencies[base]
            target_currency = created_currencies[target]
            CurrencyRate.objects.update_or_create(
                base_currency=base_currency,
                target_currency=target_currency,
                effective_date=today,
                defaults={'rate': rate}
            )

        self.stdout.write(self.style.SUCCESS('Seeded initial expenses data, currencies, and exchange rates.'))
