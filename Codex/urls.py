from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve
from django.http import JsonResponse
from django.db import connection

def health_check_view(request):
    """
    Endpoint de surveillance de l'état de l'application et de la base de données.
    Utilisable par Coolify, Docker, Traefik ou monitoring externe.
    """
    db_ok = False
    db_info = "OK"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception as e:
        db_info = f"Database error: {str(e)}"

    status_code = 200 if db_ok else 503
    return JsonResponse({
        'status': 'healthy' if db_ok else 'degraded',
        'database': db_info,
        'engine': connection.settings_dict.get('ENGINE', 'unknown').split('.')[-1],
    }, status=status_code)

urlpatterns = [
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
