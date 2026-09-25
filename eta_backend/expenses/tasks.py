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
    start_of_week = today - timedelta(days=today.weekday())

    eur_curr = Currency.objects.filter(code='EUR').first()
    usd_curr = Currency.objects.filter(code='USD').first()
    ugx_curr = Currency.objects.filter(code='UGX').first()

    if not (eur_curr and usd_curr and ugx_curr):
        return "Error: Currency models (EUR, USD, UGX) must exist in database."

    # 1. Fetch EUR -> USD rate from Frankfurter
    frankfurter_url = getattr(settings, 'FRANKFURTER_URL', 'https://api.frankfurter.dev')
    url = f"{frankfurter_url}/v1/latest?base=EUR&symbols=USD"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode())
            eur_usd_rate = Decimal(str(payload['rates']['USD']))
    except Exception:
        eur_usd_rate = Decimal('1.08')

    # 2. Look up manual/latest UGX entries from database
    latest_eur_ugx = CurrencyRate.objects.filter(
        base_currency=eur_curr,
        target_currency=ugx_curr,
        effective_date__lte=today,
    ).order_by('-effective_date', '-id').first()

    latest_usd_ugx = CurrencyRate.objects.filter(
        base_currency=usd_curr,
        target_currency=ugx_curr,
        effective_date__lte=today,
    ).order_by('-effective_date', '-id').first()

    # Determine baseline USD -> UGX and EUR -> UGX
    if latest_usd_ugx:
        usd_ugx_rate = Decimal(str(latest_usd_ugx.rate))
    else:
        usd_ugx_rate = Decimal('3700.0')

    if latest_eur_ugx:
        eur_ugx_rate = Decimal(str(latest_eur_ugx.rate))
    elif latest_usd_ugx:
        eur_ugx_rate = eur_usd_rate * usd_ugx_rate
    else:
        eur_ugx_rate = Decimal('4100.0')
        usd_ugx_rate = eur_ugx_rate / eur_usd_rate

    # Calculate remaining inverse cross-rates
    usd_eur_rate = Decimal('1.0') / eur_usd_rate
    ugx_eur_rate = Decimal('1.0') / eur_ugx_rate
    ugx_usd_rate = Decimal('1.0') / usd_ugx_rate

    # 3. Store all 6 directional exchange pairs for the current week
    rate_map = [
        (eur_curr, usd_curr, eur_usd_rate),
        (eur_curr, ugx_curr, eur_ugx_rate),
        (usd_curr, eur_curr, usd_eur_rate),
        (usd_curr, ugx_curr, usd_ugx_rate),
        (ugx_curr, eur_curr, ugx_eur_rate),
        (ugx_curr, usd_curr, ugx_usd_rate),
    ]

    for base, target, rate in rate_map:
        CurrencyRate.objects.update_or_create(
            base_currency=base,
            target_currency=target,
            effective_date=start_of_week,
            defaults={'rate': rate},
        )

    # 4. Cache multi-currency matrix
    cache_payload = {
        'EUR': {'USD': float(eur_usd_rate), 'UGX': float(eur_ugx_rate)},
        'USD': {'EUR': float(usd_eur_rate), 'UGX': float(usd_ugx_rate)},
        'UGX': {'EUR': float(ugx_eur_rate), 'USD': float(ugx_usd_rate)},
    }
    cache.set('active_weekly_rates', cache_payload, timeout=604800)

    return (
        f"Rates updated for week of {start_of_week}. "
        f"(EUR/UGX: {eur_ugx_rate}, USD/UGX: {usd_ugx_rate})"
    )


@shared_task
def send_currency_update_reminder():
    today = timezone.localdate()
    weekday = today.weekday()  # Monday = 0, Tuesday = 1

    if weekday not in (0, 1):
        return "Skipped: Reminders are only sent on Monday or Tuesday."

    start_of_week = today - timedelta(days=weekday)

    # BOTH USD->UGX AND EUR->UGX must be updated for this week to skip the reminder
    usd_ugx_updated = CurrencyRate.objects.filter(
        base_currency__code='USD',
        target_currency__code='UGX',
        effective_date__gte=start_of_week,
    ).exists()

    eur_ugx_updated = CurrencyRate.objects.filter(
        base_currency__code='EUR',
        target_currency__code='UGX',
        effective_date__gte=start_of_week,
    ).exists()

    if usd_ugx_updated and eur_ugx_updated:
        return f"Skipped: Both USD/UGX and EUR/UGX exchange rates already updated for week of {start_of_week}."

    recipient = getattr(settings, 'CURRENCY_ADMIN_EMAIL', getattr(settings, 'DEFAULT_FROM_EMAIL', None))
    if not recipient:
        return "Error: No recipient email configured."

    send_mail(
        subject=f"Reminder: Update Exchange Rates ({today.strftime('%A, %b %d, %Y')})",
        message=f"Automated reminder to check and update both USD/UGX and EUR/UGX exchange rates for week starting {start_of_week}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )

    return f"Reminder email sent to {recipient} for {today}."