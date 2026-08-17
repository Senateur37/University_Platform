from django.urls import path

from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('nouveau/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/inscription/', views.enroll, name='enroll'),
    path('<int:pk>/ressource/', views.resource_create, name='resource_create'),
]