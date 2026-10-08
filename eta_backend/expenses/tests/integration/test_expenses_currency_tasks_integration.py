import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from expenses.admin import CurrencyRateAdmin
from expenses.models import Currency, CurrencyRate
from expenses.serializers import CurrencyRateSerializer
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
        setattr(settings, 'REMINDER_RECIPIENT_EMAIL', 'admin@example.com')

        CurrencyRate.objects.create(
            base_currency=self.eur,
            target_currency=self.ugx,
            rate=Decimal('4100.0'),
            effective_date=self.start_of_week,
            is_manual=True,
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
            is_manual=True,
        )
        CurrencyRate.objects.create(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('3700.0'),
            effective_date=self.start_of_week,
            is_manual=True,
        )

        result = send_currency_update_reminder()

        self.assertIn('already updated', result.lower())
        self.assertEqual(len(mail.outbox), 0)

    @patch('django.utils.timezone.localdate')
    def test_send_currency_update_reminder_ignores_automatically_generated_rates(self, mock_localdate):
        mock_localdate.return_value = self.start_of_week
        from django.conf import settings
        settings.REMINDER_RECIPIENT_EMAIL = 'admin@example.com'

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

        self.assertIn('Reminder email sent', result)
        self.assertEqual(len(mail.outbox), 1)

    @patch('django.utils.timezone.localdate')
    def test_send_currency_update_reminder_force_sends_test_email_any_day(self, mock_localdate):
        mock_localdate.return_value = self.start_of_week + timedelta(days=3)
        from django.conf import settings
        settings.REMINDER_RECIPIENT_EMAIL = 'admin@example.com'

        CurrencyRate.objects.create(
            base_currency=self.eur,
            target_currency=self.ugx,
            rate=Decimal('4100.0'),
            effective_date=self.start_of_week,
            is_manual=True,
        )
        CurrencyRate.objects.create(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('3700.0'),
            effective_date=self.start_of_week,
            is_manual=True,
        )

        result = send_currency_update_reminder(force_send=True)

        self.assertIn('Reminder email sent', result)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[TEST] Manual Exchange Rate Reminder Trigger')

    def test_admin_entry_saves_reciprocal_for_all_supported_pairs(self):
        cases = (
            (self.usd, self.ugx, Decimal('4055'), Decimal('0.0002466091245')),
            (self.ugx, self.usd, Decimal('0.0002466'), Decimal('4055.1500405515004')),
            (self.eur, self.ugx, Decimal('4538'), Decimal('0.0002203613927')),
            (self.ugx, self.eur, Decimal('0.0002204'), Decimal('4537.2050816696915')),
        )
        admin_instance = CurrencyRateAdmin(model=CurrencyRate, admin_site=None)

        for base, target, rate, expected_reciprocal in cases:
            with self.subTest(pair=(base.code, target.code)):
                CurrencyRate.objects.all().delete()
                rate_obj = CurrencyRate(
                    base_currency=base,
                    target_currency=target,
                    rate=rate,
                    effective_date=self.start_of_week,
                )
                admin_instance.save_model(None, rate_obj, None, False)

                reciprocal = CurrencyRate.objects.get(
                    base_currency=target,
                    target_currency=base,
                    effective_date=self.start_of_week,
                )
                self.assertTrue(rate_obj.is_manual)
                self.assertTrue(reciprocal.is_manual)
                self.assertLessEqual(
                    abs(reciprocal.rate - expected_reciprocal),
                    Decimal('0.0000000001'),
                )

    def test_admin_entry_updates_existing_automatic_reciprocal(self):
        CurrencyRate.objects.create(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('3700'),
            effective_date=self.start_of_week,
        )
        CurrencyRate.objects.create(
            base_currency=self.ugx,
            target_currency=self.usd,
            rate=Decimal('0.0002500000000'),
            effective_date=self.start_of_week,
        )
        rate_obj = CurrencyRate(
            base_currency=self.usd,
            target_currency=self.ugx,
            rate=Decimal('4055'),
            effective_date=self.start_of_week,
        )

        CurrencyRateAdmin(model=CurrencyRate, admin_site=None).save_model(
            None, rate_obj, None, False
        )

        reciprocal = CurrencyRate.objects.get(
            base_currency=self.ugx,
            target_currency=self.usd,
            effective_date=self.start_of_week,
        )
        direct = CurrencyRate.objects.get(
            base_currency=self.usd,
            target_currency=self.ugx,
            effective_date=self.start_of_week,
        )
        self.assertEqual(direct.rate, Decimal('4055'))
        self.assertTrue(direct.is_manual)
        self.assertEqual(reciprocal.rate, Decimal('0.0002466091245'))
        self.assertTrue(reciprocal.is_manual)

    def test_admin_manual_checkbox_is_checked_and_not_editable(self):
        form_class = CurrencyRateAdmin(model=CurrencyRate, admin_site=None).get_form(None)
        form = form_class()

        self.assertTrue(form['is_manual'].value())
        self.assertTrue(form.fields['is_manual'].disabled)

    def test_api_rate_entry_is_manual_and_saves_reciprocal(self):
        serializer = CurrencyRateSerializer(data={
            'base_currency': self.usd.pk,
            'target_currency': self.ugx.pk,
            'rate': '4055',
            'effective_date': self.start_of_week.isoformat(),
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rate = serializer.save()

        reciprocal = CurrencyRate.objects.get(
            base_currency=self.ugx,
            target_currency=self.usd,
            effective_date=self.start_of_week,
        )
        self.assertTrue(rate.is_manual)
        self.assertTrue(reciprocal.is_manual)
        self.assertEqual(reciprocal.rate, Decimal('0.0002466091245'))
        self.assertTrue(serializer.data['is_manual'])
