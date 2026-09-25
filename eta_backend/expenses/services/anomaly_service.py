try:
    import pandas as pd
except Exception:  # pragma: no cover - pandas may be blocked by environment/DLL policy
    pd = None

from ..models import ExpenseEntry


def detect_anomalies(user):
    expenses = list(ExpenseEntry.objects.filter(user=user).values('amount', 'date', 'category__name'))
    if not expenses:
        return []

    if pd is None:
        amounts = [float(expense['amount']) for expense in expenses]
        if not amounts:
            return []
        mean = sum(amounts) / len(amounts)
        variance = sum((amount - mean) ** 2 for amount in amounts) / len(amounts)
        std = variance ** 0.5
        threshold = mean + (2 * std) if std == std else mean
        return [
            expense for expense in expenses
            if float(expense['amount']) > threshold
        ]

    df = pd.DataFrame(expenses)
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    mean = df['amount'].mean()
    std = df['amount'].std()
    threshold = mean + (2 * std) if std == std else mean
    outliers = df[df['amount'] > threshold]
    return outliers.to_dict('records')
