from django.core.management.base import BaseCommand
from expenses.models import Category, SubCategory, Item, Currency, CurrencyRate
from decimal import Decimal
from datetime import date


CATALOG = {
    'Housing': ['Rent', 'Mortgage', 'Construction', 'Other'],
    'Food': ['Proteins', 'Fruits', 'Vegetables', 'Carbohydrates', 'Oils & Spices', 'Other'],
    'Utilities': ['Electricity', 'Gas', 'Water', 'Trash Collection', 'Other'],
    'Transport': ['Taxi', 'Train', 'Bus', 'Plane', 'Other'],
    'Health Care': ['Drugs', 'Consultation', 'Medical care', 'Other'],
    'Communication': ['Internet', 'Mobile Phone', 'Landline', 'Other'],
    'Debt Payment': ['Debt Payment', 'Other'],
    'Personal Care': ['Clothing', 'Toiletries', 'Grooming Items', 'Saloon', 'Other'],
    'Leisure': ['Cinema', 'Paid TV', 'Vacation', 'Celebrations', 'Other'],
    'God': ['Tithe', 'Offertory', 'Giving', 'Other'],
    'Service (Domestic Help)': ['Service (Domestic Help)', 'Other'],
    'School': ['Fees', 'Materials', 'Eating / Allowance', 'Other'],
    'Gifts / Contributions': ['Cards', 'Money', 'Other'],
    'Furniture': ['Bed', 'Mattress', 'Pillow', 'Pillow case', 'Bed cover', 'Blanket', 'Duvet', 'Other'],
    'Electronics / Gadgets': ['Fridge', 'TV', 'Washing machine', 'Dryer', 'Phone', 'Camera', 'Laptop', 'Monitor', 'System Unit', 'Extension Cable', 'Speakers', 'Other'],
    'Stationery': ['Book', 'Journal', 'Written book', 'Pen', 'Pencil', 'Rubber', 'Ruler', 'Sharpener', 'Other'],
    'Utensils': ['Plates', 'Cups', 'Forks', 'Spoons', 'Knives', 'Cutting board', 'Glasses'],
    'Other': ['Other'],
}

CATEGORY_COLORS = [
    '#0F766E', '#2563EB', '#7C3AED', '#DB2777', '#EA580C', '#CA8A04',
    '#16A34A', '#0891B2', '#4F46E5', '#9333EA', '#BE123C', '#0284C7',
    '#65A30D', '#C2410C', '#475569', '#0D9488', '#1D4ED8', '#A16207',
]

MEASUREMENTS = {
    'Rent': 'un', 'Mortgage': 'un', 'Construction': 'un',
    'Proteins': 'kg', 'Fruits': 'kg', 'Vegetables': 'kg', 'Carbohydrates': 'kg', 'Oils & Spices': 'bt',
    'Electricity': 'un', 'Gas': 'bt', 'Water': 'ltr', 'Trash Collection': 'un',
    'Taxi': 'un', 'Train': 'un', 'Bus': 'un', 'Plane': 'un',
    'Drugs': 'pc', 'Consultation': 'un', 'Medical care': 'un',
    'Internet': 'un', 'Mobile Phone': 'un', 'Landline': 'un',
    'Debt Payment': 'un', 'Clothing': 'pc', 'Toiletries': 'pc', 'Grooming Items': 'pc', 'Saloon': 'un',
    'Cinema': 'un', 'Paid TV': 'un', 'Vacation': 'un', 'Celebrations': 'un',
    'Tithe': 'un', 'Offertory': 'un', 'Giving': 'un', 'Service (Domestic Help)': 'un',
    'Fees': 'un', 'Materials': 'pc', 'Eating / Allowance': 'un', 'Cards': 'pc', 'Money': 'un',
    'Bed': 'pc', 'Mattress': 'pc', 'Pillow': 'pc', 'Pillow case': 'pc', 'Bed cover': 'pc', 'Blanket': 'pc', 'Duvet': 'pc',
    'Fridge': 'un', 'TV': 'un', 'Washing machine': 'un', 'Dryer': 'un', 'Phone': 'un', 'Camera': 'un', 'Laptop': 'un', 'Monitor': 'un', 'System Unit': 'un', 'Extension Cable': 'pc', 'Speakers': 'un',
    'Book': 'pc', 'Journal': 'pc', 'Written book': 'pc', 'Pen': 'pc', 'Pencil': 'pc', 'Rubber': 'pc', 'Ruler': 'pc', 'Sharpener': 'pc',
    'Plates': 'pc', 'Cups': 'pc', 'Forks': 'pc', 'Spoons': 'pc', 'Knives': 'pc', 'Cutting board': 'pc', 'Glasses': 'pc',
    'Other': 'un',
}


class Command(BaseCommand):
    help = 'Seed initial categories, subcategories, items, currencies, and exchange rates.'

    def handle(self, *args, **options):
        created_categories = {}
        for index, name in enumerate(CATALOG):
            category, _ = Category.objects.update_or_create(
                name=name,
                defaults={'is_active': True, 'color': CATEGORY_COLORS[index]},
            )
            created_categories[name] = category

        Category.objects.exclude(name__in=CATALOG).update(is_active=False)

        for category_name, subcategory_names in CATALOG.items():
            category = created_categories[category_name]
            for subcategory_name in subcategory_names:
                subcategory, _ = SubCategory.objects.get_or_create(name=subcategory_name, category=category)
                Item.objects.update_or_create(
                    description=subcategory_name,
                    category=category,
                    subcategory=subcategory,
                    defaults={'measurement': MEASUREMENTS.get(subcategory_name, 'pc')},
                )

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
