from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
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

