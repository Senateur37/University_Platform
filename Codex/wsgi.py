"""
WSGI config for Codex project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Codex.settings')

# Exécution automatique des migrations sur les serveurs de production (Render / PostgreSQL)
try:
    import django
    django.setup()
    from django.core.management import call_command
    call_command('migrate', interactive=False)
except Exception as _e:
    pass

application = get_wsgi_application()

