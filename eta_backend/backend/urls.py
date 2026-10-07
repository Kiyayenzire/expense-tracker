import os

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse, HttpResponseNotAllowed
from django.urls import path, include
from django.views.decorators.cache import never_cache
from . import admin_branding

admin_path = os.getenv('DJANGO_ADMIN_URL', 'admin/').strip('/') + '/'


@never_cache
def admin_session_activity(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    return HttpResponse(status=204)


urlpatterns = [
    path(admin_path + 'session-activity/', admin_session_activity, name='admin-session-activity'),
    path(admin_path, admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # Custom accounts views take precedence (login, custom password reset, profile, account deletion)
    path('api/auth/', include('accounts.urls')),
    # Default dj_rest_auth endpoints for any leftover auth routes (e.g., logout)
    path('api/auth/', include('dj_rest_auth.urls')),
    # Registration endpoint
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    # Expenses API
    path('api/', include('expenses.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)