import json
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

    def tearDown(self):
        cache.clear()

    @patch('urllib.request.urlopen')
    def test_update_currency_rates_success(self, mock_urlopen):
        CurrencyRate.objects.create(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('3750.0'),
            effective_date=timezone.localdate(),
        )

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'rates': {'USD': 1.08}}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = update_currency_rates()

        self.assertIn('Rates updated for week', result)

        eur_usd = CurrencyRate.objects.get(base_currency=self.eur, target_currency=self.usd)
        self.assertAlmostEqual(float(eur_usd.rate), 1.08, places=4)

        eur_ugx = CurrencyRate.objects.get(base_currency=self.eur, target_currency=self.ugx)
        self.assertAlmostEqual(float(eur_ugx.rate), 4050.0, places=2)

        usd_eur = CurrencyRate.objects.get(base_currency=self.usd, target_currency=self.eur)
        self.assertAlmostEqual(float(usd_eur.rate), 1 / 1.08, places=4)

        cached_matrix = cache.get('active_weekly_rates')
        self.assertIsNotNone(cached_matrix)
        self.assertIn('EUR', cached_matrix)
        self.assertAlmostEqual(cached_matrix['EUR']['USD'], 1.08, places=4)
        self.assertAlmostEqual(cached_matrix['EUR']['UGX'], 4050.0, places=2)

    @patch('urllib.request.urlopen')
    def test_update_currency_rates_fallback_ugx(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'rates': {'USD': 1.10}}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = update_currency_rates()

        eur_ugx = CurrencyRate.objects.get(base_currency=self.eur, target_currency=self.ugx)
        self.assertAlmostEqual(float(eur_ugx.rate), 4070.0, places=2)
        self.assertIn('3700.0', result)

    def test_send_currency_update_reminder_triggers_email(self):
        from django.conf import settings

        setattr(settings, 'CURRENCY_ADMIN_EMAIL', 'admin@example.com')

        result = send_currency_update_reminder()

        self.assertIn('Reminder email sent', result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['admin@example.com'])
        self.assertIn('Update USD/UGX Exchange Rate', mail.outbox[0].subject)

    def test_send_currency_update_reminder_skips_when_updated(self):
        CurrencyRate.objects.create(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('3800.0'),
            effective_date=timezone.localdate(),
        )

        result = send_currency_update_reminder()

        self.assertIn('already updated', result)
        self.assertEqual(len(mail.outbox), 0)
