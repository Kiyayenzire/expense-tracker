import pytest


@pytest.fixture(autouse=True)
def isolate_cache_and_celery_settings(settings):
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'eta-test-in-memory-cache',
        }
    }
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
