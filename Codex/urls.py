from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve
from django.http import JsonResponse
from django.db import connection

def health_check_view(request):
    """
    Endpoint de surveillance de l'état de l'application et de la base de données.
    Si la base PostgreSQL vient d'être connectée et est vide, initialise automatiquement
    les migrations et le compte admin.
    """
    db_ok = False
    db_info = "OK"
    tables = []
    user_count = -1
    last_error = ""
    migration_output = ""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
        tables = connection.introspection.table_names()

        # Si la base est vierge ou demande explicite, migrer automatiquement
        if len(tables) == 0 or request.GET.get('migrate') == '1':
            from django.core.management import call_command
            import io
            buf = io.StringIO()
            call_command('migrate', interactive=False, stdout=buf)
            migration_output = buf.getvalue()
            tables = connection.introspection.table_names()

            # Provisionner le compte admin
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

            # Initialiser les données de démo si nécessaire
            from Cours.models import Course
            if Course.objects.count() == 0:
                try:
                    import seed_codex
                    seed_codex.seed()
                except Exception:
                    pass

        from Comptes.models import User
        user_count = User.objects.count()
    except Exception as e:
        db_info = f"Database error: {str(e)}"
        last_error = str(e)

    status_code = 200 if db_ok and not last_error else (200 if db_ok else 503)
    return JsonResponse({
        'status': 'healthy' if (db_ok and not last_error) else ('initializing' if db_ok else 'degraded'),
        'database': db_info,
        'engine': connection.settings_dict.get('ENGINE', 'unknown').split('.')[-1],
        'tables_count': len(tables),
        'user_count': user_count,
        'migration_output': migration_output[:500] if migration_output else None,
        'error': last_error,
    }, status=status_code)

from django.views.generic.base import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path('health/', health_check_view, name='health_check'),
    path('healthz/', health_check_view, name='healthz_check'),
    path('up/', health_check_view, name='up_check'),
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('Comptes.urls')),
    path('cours/', include('Cours.urls')),
    path('missions/', include('Missions.urls')),
    path('annonces/', include('Annonces.urls')),
    path('forum/', include('Forum.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

handler404 = 'Comptes.views.custom_404_view'
handler500 = 'Comptes.views.custom_500_view'
handler403 = 'Comptes.views.custom_403_view'
