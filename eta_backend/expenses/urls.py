from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    SubCategoryViewSet,
    ItemViewSet,
    CurrencyViewSet,
    CurrencyRateViewSet,
    ExpenseEntryViewSet,
    convert_currency,
    current_rates,
    export_report,
    monthly_report,
)

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('subcategories', SubCategoryViewSet, basename='subcategory')
router.register('items', ItemViewSet, basename='item')
router.register('currencies', CurrencyViewSet, basename='currency')
router.register('currency-rates', CurrencyRateViewSet, basename='currency-rate')
router.register('expenses', ExpenseEntryViewSet, basename='expense')

urlpatterns = [
    path('', include(router.urls)),
    path('rates/current/', current_rates, name='rates-current'),
    path('reports/monthly/', monthly_report, name='monthly-report'),
    path('convert-currency/', convert_currency, name='convert-currency'),
    path('export-report/', export_report, name='export-report'),
]
