from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/expenses/', include('expenses.urls')),
    path('api/auth/', include('rest_framework.urls')),  # For browsable API login/logout
]
