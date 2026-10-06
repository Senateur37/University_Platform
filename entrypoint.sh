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
python manage.py migrate --noinput || echo "WARN: Echec migrate au demarrage."

echo "==> Verification des comptes utilisateurs..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Codex.settings')
django.setup()
from Comptes.models import User
if not User.objects.filter(is_superuser=True).exists():
    try:
        import seed_codex
        seed_codex.seed()
        print('==> Initialisation des comptes (admin, prof, etudiant) effectuee avec succes.')
    except Exception as err:
        print(f'==> Note: Seed non execute: {err}')
" || echo "WARN: Verification des comptes terminee."

echo "==> Lancement du service..."
exec "$@"
