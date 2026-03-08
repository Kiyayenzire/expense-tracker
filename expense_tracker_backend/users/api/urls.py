

from django.urls import path
from .views import (
    EmailCheckView,
    RegisterView,
    ActivateUserView,
    LoginView,
    CurrentUserView,
)

urlpatterns = [
    path("check-email/", EmailCheckView.as_view(), name="check_email"),
    path("register/", RegisterView.as_view(), name="register"),
    path("activate/<uuid:token>/", ActivateUserView.as_view(), name="activate"),
    path("login/", LoginView.as_view(), name="login"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
]

