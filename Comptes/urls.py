from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('inscription/', views.register, name='register'),
    path('connexion/', views.CustomLoginView.as_view(), name='login'),
    path('mot-de-passe-oublie/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('mot-de-passe-oublie/envoye/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reinitialiser/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reinitialiser/termine/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('tableau-de-bord/', views.dashboard),
    path('profil/', views.profile_view, name='profile'),
    path('utilisateurs/', views.user_manage_view, name='user_manage'),
    path('utilisateurs/creer/', views.user_create_view, name='user_create'),
    path('utilisateurs/<int:pk>/modifier/', views.user_edit_view, name='user_edit'),
    path('utilisateurs/<int:pk>/supprimer/', views.user_delete_view, name='user_delete'),
    path('recherche/', views.search_view, name='search'),
    path('rapports/', views.reports_view, name='reports'),
]