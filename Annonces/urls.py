from django.urls import path

from . import views

urlpatterns = [
    path('', views.announcement_list, name='announcement_list'),
    path('nouvelle/', views.announcement_create, name='announcement_create'),
]