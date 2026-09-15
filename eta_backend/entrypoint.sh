#!/bin/sh
set -eu

# Execute collectstatic and superuser creation only for the web backend container
case "${1:-}" in
    gunicorn*)
        echo "Collecting static files..."
        python manage.py collectstatic --noinput

        if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
            echo "Creating superuser if non-existent..."
            python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || true
        fi
        ;;
    *)
        # Bypass static collection & superuser creation for celery and migration containers
        ;;
esac

exec "$@"