from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from users.models import CustomUser

class Category(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Expense(models.Model):
    class Currency(models.TextChoices):
        EURO = 'EUR', '€ Euro'
        USD = 'USD', '$ Dollar'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    item = models.CharField(max_length=200)
    quantity = models.IntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rate per unit")
    supplier = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, editable=False)
    currency = models.CharField(
        max_length=10,
        choices=Currency.choices,
        default=Currency.EURO
    )
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.amount = self.rate * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item} - {self.amount:.2f} {self.get_currency_display()}"

    def summary(self):
        return format_html(
            f"<strong>{self.item}</strong> from {self.supplier} ({self.country})<br>"
            f"Category: {self.category.name} | Quantity: {self.quantity} | Rate: {self.rate:.2f}<br>"
            f"Total: {self.amount:.2f} {self.get_currency_display()} on {self.date}"
        )