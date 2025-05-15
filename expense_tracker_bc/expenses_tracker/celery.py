
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_tracker_backend.settings')

app = Celery('expense_tracker_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
