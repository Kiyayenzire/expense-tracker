#!/bin/sh
set -eu

# Skip migrations, static collection, and superuser creation for Celery containers
if [ "${1:-}" != "celery" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput

    echo "Seeding predefined expense catalog..."
    python manage.py seed_initial_data

    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        echo "Creating superuser if non-existent..."
        python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || true
    fi
else
    echo "Celery container detected ($1). Skipping database migrations and static setup."
fi

exec "$@"