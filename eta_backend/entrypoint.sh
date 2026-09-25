#!/bin/sh
set -eu

# Ensure the configured default superuser exists before the app starts.
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "Ensuring default superuser exists..."
    python manage.py create_default_superuser || true
fi

# Execute collectstatic only for the web backend container.
case "${1:-}" in
    gunicorn*)
        echo "Collecting static files..."
        python manage.py collectstatic --noinput
        ;;
    *)
        # Bypass static collection for celery and migration containers.
        ;;
esac

exec "$@"