from django.urls import path

from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('nouveau/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/modifier/', views.course_edit, name='course_edit'),
    path('<int:pk>/supprimer/', views.course_delete, name='course_delete'),
    path('<int:pk>/inscription/', views.enroll, name='enroll'),
    path('<int:pk>/desinscription/', views.unenroll, name='unenroll'),
    path('<int:pk>/ressource/', views.resource_create, name='resource_create'),
    path('<int:pk>/ressource/<int:resource_pk>/supprimer/', views.resource_delete, name='resource_delete'),
    path('<int:pk>/ressource/<int:resource_pk>/telecharger/', views.resource_download, name='resource_download'),
]