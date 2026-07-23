import pandas as pd
from ..models import ExpenseEntry


def detect_anomalies(user):
    expenses = ExpenseEntry.objects.filter(user=user).values('amount', 'date', 'category__name')
    df = pd.DataFrame(expenses)
    if df.empty:
        return []
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    mean = df['amount'].mean()
    std = df['amount'].std()
    threshold = mean + (2 * std) if std == std else mean
    outliers = df[df['amount'] > threshold]
    return outliers.to_dict('records')
