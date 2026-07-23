from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=7, default='#10B981')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=64)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')

    class Meta:
        unique_together = ('name', 'category')

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Item(models.Model):
    description = models.CharField(max_length=128)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')

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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('base_currency', 'target_currency', 'effective_date')
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.base_currency.code}->{self.target_currency.code} @ {self.effective_date}"


class ExpenseEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='expenses')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='expenses')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    supplier = models.CharField(max_length=128, blank=True)
    country = models.CharField(max_length=64, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='expenses')
    user_local_time = models.DateTimeField(null=True, blank=True)
    user_timezone = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} {self.category.name} {self.amount} {self.currency.code}"
