from django.urls import path

from . import views

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('nouvelle/', views.assignment_create, name='assignment_create'),
    path('<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path('<int:pk>/modifier/', views.assignment_edit, name='assignment_edit'),
    path('<int:pk>/supprimer/', views.assignment_delete, name='assignment_delete'),
    path('<int:pk>/rendre/', views.submit_assignment, name='submit_assignment'),
    path('<int:pk>/rendus/', views.assignment_submissions, name='assignment_submissions'),
    path('<int:pk>/rendus/<int:submission_pk>/evaluer/', views.grade_submission, name='grade_submission'),
]