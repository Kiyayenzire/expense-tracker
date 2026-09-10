import os
import sys
from pathlib import Path
import environ
from celery.schedules import crontab

# ============================================================================== 
# 1. DJANGO CORE SETTINGS
# ============================================================================== 
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ['*']),
    DEFAULT_CURRENCY=(str, 'EUR'),
)

# Environment files live in the repository root, next to eta_backend.
PROJECT_ROOT = BASE_DIR.parent
env_file = PROJECT_ROOT / '.env'
dev_env_file = PROJECT_ROOT / '.env.dev'
is_pytest = any('pytest' in argument.lower() for argument in sys.argv)

if is_pytest and dev_env_file.exists():
    environ.Env.read_env(dev_env_file)
elif env_file.exists():
    environ.Env.read_env(env_file)
elif dev_env_file.exists():
    environ.Env.read_env(dev_env_file)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='dev-secret-key')
DEBUG = env('DJANGO_DEBUG', default=True)
DJANGO_ADMIN_URL = env('DJANGO_ADMIN_URL', default='admin/').strip('/') + '/'
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/1')

# Parse ALLOWED_HOSTS into a clean Python list
raw_hosts = env('DJANGO_ALLOWED_HOSTS', default='*')
if isinstance(raw_hosts, str):
    ALLOWED_HOSTS = [host.strip() for host in raw_hosts.split(',') if host.strip()]
else:
    ALLOWED_HOSTS = raw_hosts

# ============================================================================== 
# 2. DJANGO APPLICATIONS AND MIDDLEWARE
# ============================================================================== 
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'corsheaders',
    'django_celery_results',
    'django_celery_beat',
    'accounts',
    'expenses',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.SuperuserAdminMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ============================================================================== 
# 3. DATABASE CONFIGURATION
# ============================================================================== 
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# ============================================================================== 
# 4. AUTHENTICATION AND SECURITY SETTINGS
# ============================================================================== 
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 7},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = False
USE_TZ = True
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis-backed cache with a safe local-memory fallback for local/dev/test environments.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'eta-cache',
    }
}

try:
    import django_redis  # noqa: F401
except ImportError:
    pass
else:
    if env.bool('USE_REDIS_CACHE', default=True):
        CACHES['default'] = {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'eta',
        }

# ============================================================================== 
# 5. REST FRAMEWORK AND AUTH CONFIGURATION
# ============================================================================== 
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DATE_FORMAT': '%d/%m/%Y',
    'DATETIME_FORMAT': '%d/%m/%Y %H:%M',
    'DATE_INPUT_FORMATS': ['%d/%m/%Y', '%Y-%m-%d'],
}

SITE_ID = 1
AUTH_USER_MODEL = 'accounts.User'

ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['username*', 'email*']
ACCOUNT_EMAIL_VERIFICATION = env('ACCOUNT_EMAIL_VERIFICATION', default='optional')
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Expense Tracker] '
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:5173')

# Allow multiple localhost ports for development (Vite may use 5174, 5175, etc. if ports are in use)
if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:5175',
        'http://localhost:5176',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:5175',
        'http://127.0.0.1:5176',
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
    ]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ============================================================================== 
# 6. EMAIL CONFIGURATION (DEV VS PRODUCTION)
# ============================================================================== 
# Development defaults to Console backend (prints email in terminal).
# Production uses SMTP with Gmail or configured SMTP provider.
EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'no-reply@expense-tracker.local')
SERVER_EMAIL = env('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
CURRENCY_ADMIN_EMAIL = env('CURRENCY_ADMIN_EMAIL', default=DEFAULT_FROM_EMAIL)

# ============================================================================== 
# 7. EXTERNAL SERVICES AND CELERY CONFIGURATION
# ============================================================================== 
FIXER_API_KEY = env('FIXER_API_KEY', default='')
DEFAULT_CURRENCY = env('DEFAULT_CURRENCY', default='EUR')
FRANKFURTER_URL = env('FRANKFURTER_URL', default='http://rates:8080')

# Celery Timezone Settings
CELERY_TIMEZONE = 'Europe/Berlin'
CELERY_ENABLE_UTC = True

# Celery Beat Periodic Schedule
CELERY_BEAT_SCHEDULE = {
    # Task 1: Check and send email reminder if UGX rate hasn't been updated
    'send-currency-reminder-mon-tue': {
        'task': 'expenses.tasks.send_currency_update_reminder',
        'schedule': crontab(day_of_week='monday,tuesday', hour=9, minute=0),
    },
    # Task 2: Calculate and update cross-rates in DB
    'update-currency-rates-mon-tue': {
        'task': 'expenses.tasks.update_currency_rates',
        'schedule': crontab(day_of_week='monday,tuesday', hour=12, minute=0),
    },
}