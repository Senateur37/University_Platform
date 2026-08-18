from django.urls import path

from . import views

urlpatterns = [
    path('', views.announcement_list, name='announcement_list'),
    path('nouvelle/', views.announcement_create, name='announcement_create'),
    path('<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('<int:pk>/modifier/', views.announcement_edit, name='announcement_edit'),
    path('<int:pk>/supprimer/', views.announcement_delete, name='announcement_delete'),
]