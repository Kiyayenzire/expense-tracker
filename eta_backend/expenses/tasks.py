import json
import urllib.request
from datetime import timedelta
from decimal import Decimal
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone
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
    today = timezone.localdate()
    rates = {}

    # 1. Fetch EUR and USD from Frankfurter (Local Docker or Public API)
    frankfurter_url = getattr(settings, 'FRANKFURTER_URL', 'https://api.frankfurter.dev')
    url = f"{frankfurter_url}/v1/latest?base=EUR&symbols=USD"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode())
            rates['EUR'] = 1.0
            rates['USD'] = payload['rates']['USD']
    except Exception as exc:
        return f"Failed to fetch EUR/USD from Frankfurter: {str(exc)}"

    # 2. Get Currency objects from database
    eur_curr = Currency.objects.filter(code='EUR').first()
    usd_curr = Currency.objects.filter(code='USD').first()
    ugx_curr = Currency.objects.filter(code='UGX').first()

    if not (eur_curr and usd_curr and ugx_curr):
        return "Error: Currency models (EUR, USD, UGX) must exist in the database."

    # 3. Fetch the LAST ENTERED rate for EUR -> UGX in the database
    last_ugx_entry = CurrencyRate.objects.filter(
        base_currency=eur_curr,
        target_currency=ugx_curr
    ).order_by('-effective_date', '-id').first()

    if last_ugx_entry:
        eur_to_ugx = float(last_ugx_entry.rate)
    else:
        # Initial fallback if database is brand new and has no entries yet
        eur_to_ugx = 4100.0

    # Use the manually entered EUR -> UGX rate as the source of truth.
    rates['UGX'] = eur_to_ugx

    # 4. Save/Update cross-rates for the week (EUR, USD, UGX)
    symbols = ['EUR', 'USD', 'UGX']
    currency_objs = {'EUR': eur_curr, 'USD': usd_curr, 'UGX': ugx_curr}

    for source in symbols:
        for target in symbols:
            if source == target:
                continue

            rate_value = Decimal(str(rates[target] / rates[source]))

            CurrencyRate.objects.update_or_create(
                base_currency=currency_objs[source],
                target_currency=currency_objs[target],
                effective_date=today,
                defaults={'rate': rate_value},
            )

    cache_payload = {
        base: {target: float(rates[target] / rates[base]) for target in symbols}
        for base in symbols
    }
    cache.set('active_weekly_rates', cache_payload, timeout=604800)

    return f"Rates updated for week of {today}. (EUR/USD from Frankfurter, EUR/UGX carried forward from last entered rate: {eur_to_ugx})"


@shared_task
def send_currency_update_reminder():
    """
    Sends an email reminder during the Monday-Friday update window if an explicit manual EUR->UGX
    rate entry for today has not been recorded yet.
    """
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    window_end = week_start + timedelta(days=4)
    eur_curr = Currency.objects.filter(code='EUR').first()
    ugx_curr = Currency.objects.filter(code='UGX').first()

    if not (eur_curr and ugx_curr):
        return "Error: EUR or UGX currency records missing from database."

    # A Monday entry satisfies the Tuesday reminder as well.
    today_entry_exists = CurrencyRate.objects.filter(
        base_currency=eur_curr,
        target_currency=ugx_curr,
        effective_date__gte=week_start,
        effective_date__lte=window_end,
        is_manual=True,
    ).exists()

    if today_entry_exists:
        return f"EUR->UGX rate already updated for {today}. Skipping email reminder."

    recipient = getattr(settings, 'CURRENCY_ADMIN_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', None))
    if not recipient:
        return "Error: No recipient email configured in settings (CURRENCY_ADMIN_EMAIL)."

    day_name = today.strftime('%A')
    date_str = today.strftime('%b %d, %Y')

    subject = f"Reminder: Update EUR/UGX Exchange Rate ({day_name}, {date_str})"
    message = (
        f"Hello,\n\n"
        f"This is an automated reminder to check and update the EUR -> UGX exchange rate.\n\n"
        f"If Monday was a public holiday, Bank of Uganda will publish the updated rate today ({day_name}).\n\n"
        f"If no new rate is manually entered, the system will carry forward the last recorded rate.\n\n"
        f"Regards,\nExpense Tracker System"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )

    return f"Reminder email sent to {recipient} for {today}."