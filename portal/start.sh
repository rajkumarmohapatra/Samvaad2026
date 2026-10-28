#!/usr/bin/env bash
set -euo pipefail
python manage.py migrate --noinput
if [ "${DEMO_MODE:-false}" = "true" ]; then
  python manage.py bootstrap_portal --demo-if-empty
else
  python manage.py bootstrap_portal
fi
exec gunicorn samvaad.wsgi:application --bind "0.0.0.0:${PORT:-10000}" --workers 2 --threads 2 --timeout 60 --access-logfile /dev/null --error-logfile -
