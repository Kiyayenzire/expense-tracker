from django.contrib import admin
from .models import Category, SubCategory, Item, Currency, ExpenseEntry

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Item)
admin.site.register(Currency)
admin.site.register(ExpenseEntry)
