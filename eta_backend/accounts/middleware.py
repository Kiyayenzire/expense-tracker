from django.conf import settings
from django.http import HttpResponseForbidden


class SuperuserAdminMiddleware:
    """Restrict every Django admin URL to active superusers."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = f"/{settings.DJANGO_ADMIN_URL.strip('/')}/"
        if request.path == admin_path or request.path.startswith(admin_path):
            user = getattr(request, 'user', None)
            if user is not None and user.is_authenticated and not user.is_superuser:
                return HttpResponseForbidden('Only superusers can access the admin site.')
        return self.get_response(request)