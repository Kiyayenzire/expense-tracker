import pandas as pd
from sklearn.linear_model import LinearRegression
from ..models import ExpenseEntry


class ExpensePredictor:
    def __init__(self, user):
        self.user = user

    def load_data(self):
        expenses = ExpenseEntry.objects.filter(user=self.user).values('category__name', 'amount', 'date')
        df = pd.DataFrame(expenses)
        if df.empty:
            return None
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        df = df.groupby(['month', 'category__name'])['amount'].sum().reset_index()
        df.rename(columns={'category__name': 'category'}, inplace=True)
        return df

    def predict_next_month(self):
        df = self.load_data()
        if df is None:
            return {}

        predictions = {}
        for category in df['category'].unique():
            cat_data = df[df['category'] == category].copy()
            cat_data['month_index'] = cat_data['month'].apply(lambda x: x.ordinal)
            if len(cat_data) < 3:
                predictions[category] = round(cat_data['amount'].mean(), 2)
                continue
            X = cat_data[['month_index']]
            y = cat_data['amount']
            model = LinearRegression()
            model.fit(X, y)
            next_month = cat_data['month_index'].max() + 1
            predicted = model.predict([[next_month]])[0]
            predictions[category] = round(max(predicted, 0.0), 2)
        return predictions
