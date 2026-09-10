from decimal import Decimal
from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=7, default='#10B981')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=64)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')

    class Meta:
        unique_together = ('name', 'category')
        ordering = ['name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Item(models.Model):
    MEASUREMENT_CHOICES = [
        ('pc', 'Piece (pc)'),
        ('tn', 'Tin (tn)'),
        ('bt', 'Bottle (bt)'),
        ('kg', 'Kilogram (kg)'),
        ('ltr', 'Litre (ltr)'),
        ('un', 'Unit (un)'),
    ]

    description = models.CharField(max_length=128)
    measurement = models.CharField(max_length=3, choices=MEASUREMENT_CHOICES, default='pc')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')

    class Meta:
        ordering = ['description']

    def __str__(self):
        return self.description


class Currency(models.Model):
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=64)
    symbol = models.CharField(max_length=8, default='€')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class CurrencyRate(models.Model):
    base_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='base_rates')
    target_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='target_rates')
    rate = models.DecimalField(max_digits=18, decimal_places=8)
    effective_date = models.DateField()
    is_manual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('base_currency', 'target_currency', 'effective_date')
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.base_currency.code}->{self.target_currency.code} @ {self.effective_date}"


class ExpenseEntry(models.Model):
    MEASUREMENT_CHOICES = Item.MEASUREMENT_CHOICES

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='expenses')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True, related_name='expenses')
    item_description = models.CharField(max_length=128, blank=True, default='')
    measurement = models.CharField(max_length=3, choices=MEASUREMENT_CHOICES, default='pc')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    supplier = models.CharField(max_length=128, blank=True)
    country = models.CharField(max_length=64, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='expenses')
    amount_base_eur = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    applied_rate_to_eur = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    user_local_time = models.DateTimeField(null=True, blank=True)
    user_timezone = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def _resolve_rate_to_eur(self):
        if self.currency_id is None:
            return None

        if self.currency.code == 'EUR':
            return Decimal('1.0')

        direct_rate = CurrencyRate.objects.filter(
            base_currency=self.currency,
            target_currency__code='EUR',
            effective_date__lte=self.date,
        ).order_by('-effective_date', '-id').first()

        if direct_rate is not None:
            return Decimal(str(direct_rate.rate))

        reverse_rate = CurrencyRate.objects.filter(
            base_currency__code='EUR',
            target_currency=self.currency,
            effective_date__lte=self.date,
        ).order_by('-effective_date', '-id').first()

        if reverse_rate and reverse_rate.rate != 0:
            return Decimal('1') / Decimal(str(reverse_rate.rate))

        return Decimal('1.0')

    def save(self, *args, **kwargs):
        if self.amount is not None and self.currency_id and (self.amount_base_eur is None or self.applied_rate_to_eur is None):
            rate = self._resolve_rate_to_eur()
            if rate is not None:
                self.applied_rate_to_eur = Decimal(str(rate))
                self.amount_base_eur = (self.amount * Decimal(str(rate))).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} {self.category.name} {self.amount} {self.currency.code}"
