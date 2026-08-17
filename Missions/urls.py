from django.urls import path

from . import views

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('nouvelle/', views.assignment_create, name='assignment_create'),
    path('<int:pk>/rendre/', views.submit_assignment, name='submit_assignment'),
]