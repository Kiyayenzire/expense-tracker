


# expenses/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, SubCategoryViewSet, ExpenseViewSet, ExchangeRateViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('subcategories', SubCategoryViewSet, basename='subcategories')
router.register('expenses', ExpenseViewSet, basename='expenses')
router.register('exchange-rates', ExchangeRateViewSet, basename='exchange-rates')

urlpatterns = [
    path('', include(router.urls)),
]







