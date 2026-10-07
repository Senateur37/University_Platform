release: python manage.py migrate --noinput
web: python manage.py migrate --noinput && gunicorn Codex.wsgi:application

