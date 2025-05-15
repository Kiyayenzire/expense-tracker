from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ExpenseViewSet, ExpenseExportView

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('expenses', ExpenseViewSet, basename='expenses')

urlpatterns = [
    path('', include(router.urls)),
    path('expenses/export/', ExpenseExportView.as_view(), name='export-expenses'),
]
