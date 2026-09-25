from decimal import Decimal
from datetime import date

import pytest

from expenses.admin import CurrencyRateAdmin
from expenses.models import Currency, CurrencyRate
from expenses.services.currency_service import CurrencyService


@pytest.mark.unit
class TestCurrencyService:
    def test_get_latest_rate_same_currency(self):
        rate = CurrencyService.get_latest_rate('EUR', 'EUR')
        assert rate == 1.0

    @pytest.mark.django_db
    def test_get_latest_rate_from_database(self, currency_rate):
        rate = CurrencyService.get_latest_rate('EUR', 'USD')
        assert rate == 1.1

    @pytest.mark.django_db
    def test_convert_amount(self, currency_rate):
        amount = Decimal('100')
        converted = CurrencyService.convert_amount(amount, 'EUR', 'USD')
        assert converted == Decimal('110')

    @pytest.mark.django_db
    def test_convert_amount_invalid_input(self, currency_rate):
        converted = CurrencyService.convert_amount('invalid', 'EUR', 'USD')
        assert converted is None

    @pytest.mark.django_db
    def test_save_rate(self, currency, usd_currency):
        rate_obj = CurrencyService.save_rate('EUR', 'USD', Decimal('1.15'))
        assert rate_obj is not None
        assert rate_obj.rate == Decimal('1.15')
        assert CurrencyRate.objects.filter(
            base_currency__code='EUR',
            target_currency__code='USD',
        ).exists()

    @pytest.mark.django_db
    def test_get_rate_history(self, currency_rate):
        history = CurrencyService.get_rate_history('EUR', 'USD', limit=10)
        assert isinstance(history, list)

    @pytest.mark.django_db
    def test_currency_rate_model(self, currency_rate):
        assert currency_rate.rate == Decimal('1.10')
        assert currency_rate.base_currency.code == 'EUR'
        assert currency_rate.target_currency.code == 'USD'

    @pytest.mark.django_db
    def test_currency_unique_code(self, db):
        Currency.objects.create(code='EUR', name='Euro')
        with pytest.raises(Exception):
            Currency.objects.create(code='EUR', name='European Union')

    @pytest.mark.django_db
    def test_currency_rate_unique_together(self, currency, usd_currency, db):
        CurrencyRate.objects.create(
            base_currency=currency,
            target_currency=usd_currency,
            rate=Decimal('1.10'),
            effective_date=date.today(),
        )
        with pytest.raises(Exception):
            CurrencyRate.objects.create(
                base_currency=currency,
                target_currency=usd_currency,
                rate=Decimal('1.15'),
                effective_date=date.today(),
            )

    @pytest.mark.django_db
    def test_currency_rate_supports_thirteen_decimal_places(self, currency, db):
        ugx_currency = Currency.objects.create(code='UGX', name='Ugandan Shilling', symbol='USh', is_active=True)

        rate_obj = CurrencyRate.objects.create(
            base_currency=currency,
            target_currency=ugx_currency,
            rate=Decimal('4100.0001234567890'),
            effective_date=date.today(),
        )

        assert rate_obj.rate == Decimal('4100.0001234567890')

    @pytest.mark.django_db
    def test_currency_rate_admin_uses_thirteen_decimal_places(self):
        admin_instance = CurrencyRateAdmin(model=CurrencyRate, admin_site=None)
        form_class = admin_instance.get_form(None)
        rate_field = form_class.base_fields['rate']

        assert rate_field.decimal_places == 13
