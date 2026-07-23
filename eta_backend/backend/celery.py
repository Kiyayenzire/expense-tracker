import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
app = Celery('backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-currency-rates-every-monday-17': {
        'task': 'expenses.tasks.update_currency_rates',
        'schedule': crontab(hour=17, minute=0, day_of_week='mon'),
    },
}
