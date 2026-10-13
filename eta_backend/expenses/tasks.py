import json
import logging
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

logger = logging.getLogger(__name__)


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

    def latest_rate(base_currency, target_currency, *, manual_only=False, current_week=False):
        rates = CurrencyRate.objects.filter(
            base_currency=base_currency,
            target_currency=target_currency,
            effective_date__lte=today,
        )
        if manual_only:
            rates = rates.filter(is_manual=True)
        if current_week:
            rates = rates.filter(effective_date__gte=start_of_week)
        else:
            rates = rates.filter(effective_date__lt=start_of_week)
        return rates.order_by('-effective_date', '-id').first()

    def resolve_rate(base_currency, target_currency):
        for manual_only, current_week in (
            (True, True),
            (True, False),
            (False, False),
            (False, True),
        ):
            for source, target, reciprocal in (
                (base_currency, target_currency, False),
                (target_currency, base_currency, True),
            ):
                rate = latest_rate(
                    source,
                    target,
                    manual_only=manual_only,
                    current_week=current_week,
                )
                if rate and rate.rate:
                    value = Decimal(str(rate.rate))
                    return Decimal('1') / value if reciprocal else value
        return None

    # 1. Fetch EUR -> USD rate from Frankfurter
    frankfurter_url = getattr(settings, 'FRANKFURTER_URL', 'https://api.frankfurter.dev')
    url = f"{frankfurter_url}/v1/latest?base=EUR&symbols=USD"

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode())
            eur_usd_rate = Decimal(str(payload['rates']['USD']))
        if eur_usd_rate <= 0:
            raise ValueError('Frankfurter returned a non-positive EUR/USD rate.')
    except Exception as exc:
        logger.warning("Unable to retrieve the EUR/USD exchange rate from Frankfurter: %s", exc)
        eur_usd_rate = resolve_rate(eur_curr, usd_curr)

    # Prefer this week's manual rates, then the last manual rate. Generated
    # snapshots are fallbacks only, so they cannot supersede a manual update.
    eur_ugx_rate = resolve_rate(eur_curr, ugx_curr)
    usd_ugx_rate = resolve_rate(usd_curr, ugx_curr)

    if eur_usd_rate is None and eur_ugx_rate and usd_ugx_rate:
        eur_usd_rate = eur_ugx_rate / usd_ugx_rate
    if eur_usd_rate is None:
        return "Error: No EUR/USD exchange rate is available from the provider or saved rates."
    if eur_ugx_rate is None and usd_ugx_rate is not None:
        eur_ugx_rate = eur_usd_rate * usd_ugx_rate
    if usd_ugx_rate is None and eur_ugx_rate is not None:
        usd_ugx_rate = eur_ugx_rate / eur_usd_rate
    if eur_ugx_rate is None or usd_ugx_rate is None:
        return "Error: No EUR/UGX or USD/UGX exchange rate is available from saved rates."

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
        manual_current_week = CurrencyRate.objects.filter(
            base_currency=base,
            target_currency=target,
            effective_date__gte=start_of_week,
            effective_date__lte=today,
            is_manual=True,
        ).exists()
        if manual_current_week:
            continue
        CurrencyRate.objects.update_or_create(
            base_currency=base,
            target_currency=target,
            effective_date=start_of_week,
            defaults={'rate': rate, 'is_manual': False},
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
def send_currency_update_reminder(force_send=False):
    today = timezone.localdate()
    weekday = today.weekday()  # Monday = 0, Tuesday = 1

    if weekday not in (0, 1) and not force_send:
        return "Skipped: Reminders are only sent on Monday or Tuesday."

    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    required_pairs = (('USD', 'UGX'), ('EUR', 'UGX'))
    missing_pairs = [
        f'{base}/{target}'
        for base, target in required_pairs
        if not CurrencyRate.objects.filter(
            base_currency__code=base,
            target_currency__code=target,
            effective_date__gte=start_of_week,
            effective_date__lte=end_of_week,
            is_manual=True,
        ).exists()
    ]

    if not missing_pairs and not force_send:
        return f"Skipped: Both USD/UGX and EUR/UGX exchange rates already updated for week of {start_of_week}."

    recipient = settings.REMINDER_RECIPIENT_EMAIL
    if not recipient:
        return "Error: No recipient email configured."

    if force_send:
        subject = "[TEST] Manual Exchange Rate Reminder Trigger"
        missing_status = (
            f"Missing manually updated rate pair(s): {', '.join(missing_pairs)}."
            if missing_pairs
            else "Both required manually updated rate pairs are present for the current week."
        )
        message = (
            "This is a manual test of the exchange rate reminder email system.\n\n"
            f"{missing_status}\n\n"
            "This test email was sent because force_send=True."
        )
    else:
        missing_str = ', '.join(missing_pairs)
        subject = f"Action required: Missing exchange rates ({missing_str})"
        message = (
            f"The exchange rate update for the week of {start_of_week:%B %d, %Y} is incomplete.\n"
            f"Missing manually updated rate pair(s): {missing_str}.\n\n"
            "Please review or update the rates on https://eta.althech.com."
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
    logger.info("Exchange rate reminder email sent to %s.", recipient)
    return f"Reminder email sent to {recipient} for {today}."