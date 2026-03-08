

# expenses/models.py
from django.db import models
from django.utils.html import format_html
from users.models import CustomUser
from decimal import Decimal
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

# ------------------------------
# Category model
# ------------------------------
class Category(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# ------------------------------
# SubCategory model
# ------------------------------
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name} → {self.name}"

# ------------------------------
# Expense model
# ------------------------------
class Expense(models.Model):
    class Currency(models.TextChoices):
        EURO = 'EUR', '€'
        USD = 'USD', '$'
        UGX = 'UGX', 'UGX'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, editable=False)
    category = models.ForeignKey("Category", on_delete=models.CASCADE)
    subcategory = models.ForeignKey(
        "SubCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses"
    )
    item = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, default="pcs")
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Rate per unit")
    supplier = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, editable=False)
    currency = models.CharField(max_length=10, choices=Currency.choices, default=Currency.EURO)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    # ------------------------------
    # Auto-calculate amount
    # ------------------------------
    def save(self, *args, **kwargs):
        qty = self.quantity or Decimal("1")
        self.amount = (self.rate or Decimal("0.00")) * qty
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item} - {self.amount:.2f} {self.get_currency_display()}"

    def summary(self):
        subcat_text = f" / {self.subcategory.name}" if self.subcategory else ""
        return format_html(
            f"<strong>{self.item}</strong> from {self.supplier or 'N/A'} ({self.country or 'N/A'})<br>"
            f"Category: {self.category.name}{subcat_text} | Quantity: {self.quantity} {self.unit} | Rate: {self.rate:.2f}<br>"
            f"Total: {self.amount:.2f} {self.get_currency_display()} on {self.date}"
        )

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["date"]),
            models.Index(fields=["category"]),
        ]

# ------------------------------
# ExchangeRate model
# ------------------------------
class ExchangeRate(models.Model):
    currency_from = models.CharField(max_length=3)  # e.g., 'EUR'
    currency_to = models.CharField(max_length=3)    # e.g., 'USD'
    rate = models.DecimalField(max_digits=12, decimal_places=6)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('currency_from', 'currency_to')

    def __str__(self):
        return f"1 {self.currency_from} → {self.rate} {self.currency_to} (updated {self.updated_at.date()})"
    


