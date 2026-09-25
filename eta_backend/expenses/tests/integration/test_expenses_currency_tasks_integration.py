import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from expenses.models import Currency, CurrencyRate
from expenses.tasks import send_currency_update_reminder, update_currency_rates


class CurrencyTaskTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.eur = Currency.objects.create(code='EUR', name='Euro', symbol='€')
        self.usd = Currency.objects.create(code='USD', name='US Dollar', symbol='$')
        self.ugx = Currency.objects.create(code='UGX', name='Ugandan Shilling', symbol='USh')
        today = timezone.localdate()
        self.start_of_week = today - timedelta(days=today.weekday())

    def tearDown(self):
        cache.clear()

    @patch('urllib.request.urlopen')
    def test_update_currency_rates_with_usd_ugx_in_db(self, mock_urlopen):
        CurrencyRate.objects.create(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('3750.0'),
            effective_date=self.start_of_week,
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'rates': {'USD': 1.08}}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = update_currency_rates()

        self.assertIn('Rates updated for week', result)

        eur_ugx = CurrencyRate.objects.get(base_currency=self.eur, target_currency=self.ugx)
        self.assertAlmostEqual(float(eur_ugx.rate), 4050.0, places=2)

        ugx_usd = CurrencyRate.objects.get(base_currency=self.ugx, target_currency=self.usd)
        self.assertAlmostEqual(float(ugx_usd.rate), 1 / 3750.0, places=6)

    @patch('urllib.request.urlopen')
    def test_update_currency_rates_with_eur_ugx_in_db(self, mock_urlopen):
        CurrencyRate.objects.create(
            base_currency=self.eur,
            target_currency=self.ugx,
            rate=Decimal('4200.0'),
            effective_date=self.start_of_week,
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'rates': {'USD': 1.05}}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        update_currency_rates()

        eur_ugx = CurrencyRate.objects.get(base_currency=self.eur, target_currency=self.ugx)
        self.assertEqual(eur_ugx.rate, Decimal('4200.0'))

    @patch('urllib.request.urlopen')
    def test_update_currency_rates_fallback_defaults(self, mock_urlopen):
        mock_urlopen.side_effect = Exception('API down')

        update_currency_rates()

        eur_ugx = CurrencyRate.objects.get(base_currency=self.eur, target_currency=self.ugx)
        self.assertEqual(eur_ugx.rate, Decimal('4100.0'))

        usd_ugx = CurrencyRate.objects.get(base_currency=self.usd, target_currency=self.ugx)
        self.assertAlmostEqual(float(usd_ugx.rate), 4100.0 / 1.08, places=2)

    @patch('django.utils.timezone.localdate')
    def test_send_currency_update_reminder_triggers_when_only_one_updated(self, mock_localdate):
        mock_localdate.return_value = self.start_of_week

        from django.conf import settings
        setattr(settings, 'CURRENCY_ADMIN_EMAIL', 'admin@example.com')

        CurrencyRate.objects.create(
            base_currency=self.eur,
            target_currency=self.ugx,
            rate=Decimal('4100.0'),
            effective_date=self.start_of_week,
        )

        result = send_currency_update_reminder()

        self.assertIn('Reminder email sent', result)
        self.assertEqual(len(mail.outbox), 1)

    @patch('django.utils.timezone.localdate')
    def test_send_currency_update_reminder_skips_when_both_updated(self, mock_localdate):
        mock_localdate.return_value = self.start_of_week

        CurrencyRate.objects.create(
            base_currency=self.eur,
            target_currency=self.ugx,
            rate=Decimal('4100.0'),
            effective_date=self.start_of_week,
        )
        CurrencyRate.objects.create(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('3700.0'),
            effective_date=self.start_of_week,
        )

        result = send_currency_update_reminder()

        self.assertIn('already updated', result.lower())
        self.assertEqual(len(mail.outbox), 0)
