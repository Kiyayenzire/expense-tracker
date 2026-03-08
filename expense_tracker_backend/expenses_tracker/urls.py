

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from expenses.api.views import test_connection

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [

    path("admin/", admin.site.urls),

    # Root - redirect to frontend email check page
    path(
        "",
        RedirectView.as_view(
            url="http://127.0.0.1:5173/check-email",
            permanent=False,
        ),
    ),

    # Test endpoint
    path("api/test/", test_connection),

    # User APIs
    path("api/users/", include("users.api.urls")),

    # JWT login
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # Expenses API
    path(
        "api/expenses/",
        include("expenses.api.urls"),
    ),
]


