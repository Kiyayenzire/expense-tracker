"""
Currency Service - Business logic for currency conversion and management.
Separates currency logic from view layer.
"""
import json
import urllib.request
from decimal import Decimal, InvalidOperation
from django.conf import settings
from ..models import Currency, CurrencyRate
from datetime import date


class CurrencyService:
    """Service for currency conversion and management."""
    
    @staticmethod
    def get_latest_rate(base: str, target: str) -> float:
        """
        Get the latest exchange rate between two currencies.
        """
        return float(CurrencyService.get_rate_for_date(base, target, date.today()) or 1.0)

    @staticmethod
    def get_rate_for_date(base: str, target: str, effective_date: date = None) -> float:
        """
        Get the exchange rate between two currencies for a specific date.
        """
        if base == target:
            return 1.0

        if effective_date is None:
            effective_date = date.today()

        db_rate = CurrencyRate.objects.filter(
            base_currency__code=base,
            target_currency__code=target,
            effective_date__lte=effective_date,
        ).order_by('-effective_date').first()

        if db_rate:
            return float(db_rate.rate)

        reverse_rate = CurrencyRate.objects.filter(
            base_currency__code=target,
            target_currency__code=base,
            effective_date__lte=effective_date,
        ).order_by('-effective_date').first()

        if reverse_rate and reverse_rate.rate != 0:
            return float(1 / reverse_rate.rate)

        external_rate = CurrencyService._fetch_from_api(base, target)
        if external_rate is not None:
            try:
                CurrencyService.save_rate(base, target, Decimal(str(external_rate)), effective_date)
            except Exception:
                pass
            return external_rate

        return None

    @staticmethod
    def _fetch_from_api(base: str, target: str) -> float:
        """
        Fetch exchange rate from external API.
        
        Args:
            base: Base currency code
            target: Target currency code
            
        Returns:
            Exchange rate or None
        """
        try:
            url = (
                f"http://data.fixer.io/api/latest?"
                f"access_key={settings.FIXER_API_KEY}&"
                f"symbols={base},{target}&format=1"
            )
            with urllib.request.urlopen(url, timeout=10) as response:
                payload = json.loads(response.read().decode())
                rates = payload.get('rates', {})
                if base in rates and target in rates:
                    return rates[target] / rates[base]
        except Exception:
            return None
        
        return None
    
    @staticmethod
    def convert_amount(amount: Decimal, base: str, target: str, effective_date: date = None) -> Decimal:
        """
        Convert an amount from one currency to another using the rate for a specific date.
        
        Args:
            amount: Amount to convert
            base: Base currency code
            target: Target currency code
            effective_date: Date to resolve the exchange rate
            
        Returns:
            Converted amount or None if conversion not possible
        """
        try:
            amount_decimal = Decimal(str(amount))
        except (ValueError, TypeError, InvalidOperation):
            return None

        rate = CurrencyService.get_rate_for_date(base, target, effective_date)
        if rate is None:
            return None

        rate_decimal = Decimal(str(rate))
        result = amount_decimal * rate_decimal
        return result.quantize(Decimal('0.01'))
    
    @staticmethod
    def save_rate(base_code: str, target_code: str, rate: Decimal, 
                  effective_date: date = None) -> CurrencyRate:
        """
        Save an exchange rate to the database.
        
        Args:
            base_code: Base currency code
            target_code: Target currency code
            rate: Exchange rate
            effective_date: Date of the rate. Defaults to today.
            
        Returns:
            Created CurrencyRate instance
        """
        if effective_date is None:
            effective_date = date.today()
        
        base_currency = Currency.objects.get(code=base_code)
        target_currency = Currency.objects.get(code=target_code)
        
        rate_obj, created = CurrencyRate.objects.update_or_create(
            base_currency=base_currency,
            target_currency=target_currency,
            effective_date=effective_date,
            defaults={'rate': rate}
        )
        return rate_obj
    
    @staticmethod
    def get_rate_history(base_code: str, target_code: str, 
                        limit: int = 10) -> list:
        """
        Get historical exchange rates.
        
        Args:
            base_code: Base currency code
            target_code: Target currency code
            limit: Number of recent rates to return
            
        Returns:
            List of CurrencyRate objects ordered by date (newest first)
        """
        return list(CurrencyRate.objects.filter(
            base_currency__code=base_code,
            target_currency__code=target_code,
        ).order_by('-effective_date')[:limit])
