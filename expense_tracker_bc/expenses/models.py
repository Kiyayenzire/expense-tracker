from django.db import models
from users.models import CustomUser

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    quantity = models.FloatField()
    supplier = models.CharField(max_length=100)
    country = models.CharField(max_length=50)
    amount = models.FloatField()
    currency = models.CharField(max_length=10, default='EUR')
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item} - {self.amount} {self.currency}"
