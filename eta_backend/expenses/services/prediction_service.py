try:
    import pandas as pd
except Exception:  # pragma: no cover - pandas may be blocked by environment/DLL policy
    pd = None

from django.db.models import Count

from ..models import ExpenseEntry
from .currency_service import CurrencyService

try:
    from sklearn.linear_model import LinearRegression
except ImportError:  # pragma: no cover - fallback when sklearn is unavailable
    LinearRegression = None


class ExpensePredictor:
    def __init__(self, user):
        self.user = user

    def load_data(self, target_currency='EUR'):
        expenses = ExpenseEntry.objects.filter(user=self.user).select_related('currency').values('category__name', 'amount', 'quantity', 'date', 'currency__code')
        rows = []
        for expense in expenses:
            line_total = expense['amount'] * (expense['quantity'] or 1)
            converted = CurrencyService.convert_amount(line_total, expense['currency__code'], target_currency, expense['date']) or 0
            rows.append({'category__name': expense['category__name'], 'amount': float(converted), 'date': expense['date'], 'quantity': 1})

        if not rows:
            return None

        if pd is None:
            grouped = {}
            for row in rows:
                category = row['category__name']
                month = row['date'].strftime('%Y-%m') if hasattr(row['date'], 'strftime') else str(row['date'])[:7]
                key = (month, category)
                grouped[key] = grouped.get(key, 0.0) + float(row['amount'])
            return [
                {'month': month, 'category': category, 'amount': value}
                for (month, category), value in grouped.items()
            ]

        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0) * pd.to_numeric(df['quantity'], errors='coerce').fillna(1)
        df['month'] = df['date'].dt.to_period('M')
        df = df.groupby(['month', 'category__name'])['amount'].sum().reset_index()
        df.rename(columns={'category__name': 'category'}, inplace=True)
        return df

    def predict_next_month(self, target_currency='EUR'):
        df = self.load_data(target_currency)
        if df is None:
            return {'predictions': {}, 'high_volume_categories': []}

        entry_counts = dict(
            ExpenseEntry.objects.filter(user=self.user)
            .values('category__name')
            .annotate(entry_count=Count('id'))
            .values_list('category__name', 'entry_count')
        )

        if pd is None:
            category_totals = {}
            for row in df:
                category = row['category']
                category_totals[category] = category_totals.get(category, 0.0) + float(row.get('amount', 0))
            predictions = {category: round(total, 2) for category, total in category_totals.items()}
        else:
            predictions = {}
            for category in df['category'].unique():
                cat_data = df[df['category'] == category].copy()
                cat_data['month_index'] = cat_data['month'].apply(lambda x: x.ordinal)
                if len(cat_data) < 3 or LinearRegression is None:
                    predictions[category] = float(round(cat_data['amount'].mean(), 2))
                    continue
                X = cat_data[['month_index']]
                y = cat_data['amount']
                model = LinearRegression()
                model.fit(X, y)
                next_month = cat_data['month_index'].max() + 1
                predicted = model.predict([[next_month]])[0]
                predictions[category] = float(round(max(predicted, 0.0), 2))

        high_volume_categories = [
            {
                'category': category,
                'entry_count': count,
                'forecast': float(predictions.get(category, 0)),
            }
            for category, count in sorted(entry_counts.items(), key=lambda item: item[1], reverse=True)
            if count >= 11
        ]
        return {
            'predictions': predictions,
            'high_volume_categories': high_volume_categories,
        }
