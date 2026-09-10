import pandas as pd
from django.db.models import Count
from sklearn.linear_model import LinearRegression
from ..models import ExpenseEntry
from .currency_service import CurrencyService


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
        df = pd.DataFrame(rows)
        if df.empty:
            return None
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

        predictions = {}
        entry_counts = dict(
            ExpenseEntry.objects.filter(user=self.user)
            .values('category__name')
            .annotate(entry_count=Count('id'))
            .values_list('category__name', 'entry_count')
        )
        for category in df['category'].unique():
            cat_data = df[df['category'] == category].copy()
            cat_data['month_index'] = cat_data['month'].apply(lambda x: x.ordinal)
            if len(cat_data) < 3:
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
