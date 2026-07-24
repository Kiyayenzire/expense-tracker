import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
    DEFAULT_CURRENCY=(str, 'EUR'),
)

env_file = BASE_DIR.parent / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)
else:
    dev_env_file = BASE_DIR.parent / '.env.dev'
    if dev_env_file.exists():
        environ.Env.read_env(dev_env_file)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='dev-secret-key')
DEBUG = env('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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

DATABASE_URL = env('DATABASE_URL', default='')
if DATABASE_URL:
    DATABASES = {
        'default': env.db()
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DATABASE_NAME', default='expense_tracker'),
            'USER': env('DATABASE_USER', default='expense_user'),
            'PASSWORD': env('DATABASE_PASSWORD', default='expense_password'),
            'HOST': env('DATABASE_HOST', default='db'),
            'PORT': env('DATABASE_PORT', default='5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
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
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

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
ACCOUNT_LOGIN_METHODS = ['username']
ACCOUNT_SIGNUP_FIELDS = ['username', 'email', 'password1', 'password2']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Expense Tracker] '
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

FIXER_API_KEY = env('FIXER_API_KEY', default='')
DEFAULT_CURRENCY = env('DEFAULT_CURRENCY', default='EUR')

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://redis:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://redis:6379/2')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
