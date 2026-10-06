FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Anti rétro-ingénierie : on ne garde que le bytecode du code applicatif,
# on supprime les sources .py, les scripts de seed/build et les tests.
# `manage.py check` fait échouer le build si le code compilé est inutilisable.
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && python -m compileall -b -q Codex Comptes Cours Missions Annonces Forum \
    && find Codex Comptes Cours Missions Annonces Forum -name '*.py' -delete \
    && find . -name '__pycache__' -type d -prune -exec rm -rf {} + \
    && rm -rf seed_codex.py Procfile build.sh runtime.txt .git .env.example Dockerfile docker-compose.yml \
    && SECRET_KEY=build-only python manage.py check \
    && mkdir -p /app/media \
    && chown -R app:app /app/media /app/staticfiles \
    && chmod -R a-w /app --exclude=media 2>/dev/null || true \
    && chmod +x /app/entrypoint.sh

USER app

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "Codex.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--worker-tmp-dir", "/dev/shm", "--limit-request-line", "4094", "--access-logfile", "-"]
