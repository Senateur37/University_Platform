#!/bin/sh
set -e

echo "==> Initialisation de la plateforme Codex..."

# Attendre que la base de donnees reponde (utile quand PostgreSQL demarre en meme temps)
python -c "
import time, os, sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Codex.settings')
django.setup()
from django.db import connection

for attempt in range(1, 16):
    try:
        connection.ensure_connection()
        print(f'Connexion a la base de donnees etablie avec succes ({connection.settings_dict.get(\"ENGINE\")}).')
        sys.exit(0)
    except Exception as e:
        print(f'Attente de la base de donnees ({attempt}/15)... ({e})')
        time.sleep(2)
print('ATTENTION: Delai d attente de base depasse, tentative de migration...')
"

echo "==> Application des migrations..."
python manage.py migrate --noinput

echo "==> Configuration du compte super-administrateur..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Codex.settings')
django.setup()
from Comptes.models import User
admin_user, _ = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@university.edu',
        'first_name': 'Administrateur',
        'last_name': 'Principal',
        'user_type': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'is_validated': True,
        'filiere': 'Direction',
    }
)
admin_user.set_password('admin123')
admin_user.is_staff = True
admin_user.is_superuser = True
admin_user.is_validated = True
admin_user.user_type = 'admin'
admin_user.save()
print('==> Compte admin configure: admin / admin123')

# Si aucun cours n'existe, initialiser les donnees de demonstration
from Cours.models import Course
if Course.objects.count() == 0:
    try:
        import seed_codex
        seed_codex.seed()
        print('==> Donnees de demonstration initialisees.')
    except Exception as e:
        print(f'==> Note seed: {e}')
"

echo "==> Lancement du service..."
exec "$@"
