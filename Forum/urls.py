from django.urls import path
from . import views

urlpatterns = [
    path('', views.topic_list, name='topic_list'),
    path('nouveau/', views.topic_create, name='topic_create'),
    path('<int:pk>/', views.topic_detail, name='topic_detail'),
    path('<int:pk>/modifier/', views.topic_edit, name='topic_edit'),
    path('<int:pk>/supprimer/', views.topic_delete, name='topic_delete'),
    path('<int:pk>/repondre/', views.post_create, name='post_create'),
    path('<int:pk>/reponse/<int:post_pk>/supprimer/', views.post_delete, name='post_delete'),
    path('<int:pk>/epingler/', views.topic_toggle_pin, name='topic_toggle_pin'),
    path('<int:pk>/verrouiller/', views.topic_toggle_close, name='topic_toggle_close'),
]
