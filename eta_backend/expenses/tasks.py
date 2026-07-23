import json
import urllib.request
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import date
from .models import Currency, CurrencyRate
from .services.prediction_service import ExpensePredictor


@shared_task
def calculate_predictions(user_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(id=user_id).first()
    if not user:
        return {}
    predictor = ExpensePredictor(user)
    return predictor.predict_next_month()


@shared_task
def update_currency_rates():
    today = date.today()
    if today.weekday() != 0 or timezone.now().hour < 17:
        return 'scheduled only on Monday evening'

    symbols = ['EUR', 'USD', 'UGX']
    if settings.FIXER_API_KEY:
        url = f"http://data.fixer.io/api/latest?access_key={settings.FIXER_API_KEY}&symbols={','.join(symbols)}"
    else:
        url = f"https://api.exchangerate.host/latest?symbols={','.join(symbols)}&base=EUR"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode())
            rates = payload.get('rates', {})
            base = payload.get('base', 'EUR')
            if 'EUR' not in rates:
                rates['EUR'] = 1.0
            for source in symbols:
                for target in symbols:
                    if source == target:
                        continue
                    if source in rates and target in rates:
                        rate_value = rates[target] / rates[source]
                        base_currency = Currency.objects.filter(code=source).first()
                        target_currency = Currency.objects.filter(code=target).first()
                        if base_currency and target_currency:
                            CurrencyRate.objects.update_or_create(
                                base_currency=base_currency,
                                target_currency=target_currency,
                                effective_date=today,
                                defaults={'rate': rate_value},
                            )
            return 'rates updated'
    except Exception as exc:
        return str(exc)
