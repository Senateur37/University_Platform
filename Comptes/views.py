import csv
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q, Avg, Count
from django import forms

from .models import User, Notification
from .decorateurs import user_type_required


class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        remember_me = self.request.POST.get('remember_me')
        if remember_me:
            self.request.session.set_expiry(1209600)  # 14 jours
        else:
            self.request.session.set_expiry(0)  # À la fermeture du navigateur
        return super().form_valid(form)
from Cours.models import Course
from Missions.models import Assignment, Submission
from Annonces.models import Announcement


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password_confirmation = forms.CharField(widget=forms.PasswordInput, label="Confirmation du mot de passe")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'filiere', 'user_type', 'bio')
        labels = {
            'username': "Nom d'utilisateur",
            'email': 'Adresse email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'filiere': 'Filière / Département',
            'user_type': 'Rôle sur le campus',
            'bio': 'Présentation / Bio',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].choices = [choice for choice in self.fields['user_type'].choices if choice[0] != 'admin']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirmation'):
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if user.user_type == 'admin':
            user.is_staff = True
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'filiere', 'bio', 'avatar')
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Adresse email',
            'filiere': 'Filière / Département',
            'bio': 'Biographie',
            'avatar': 'Photo de profil (Optionnel)',
        }


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, label="Mot de passe (Laisser vide pour conserver l'actuel)")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'filiere', 'is_validated', 'bio')
        labels = {
            'username': "Nom d'utilisateur",
            'email': 'Adresse email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'user_type': 'Rôle sur le campus',
            'filiere': 'Filière / Département',
            'is_validated': 'Compte validé / approuvé',
            'bio': 'Biographie',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            user.set_password(pwd)
        if user.user_type == 'admin':
            user.is_staff = True
        else:
            if not user.is_superuser:
                user.is_staff = False
        if commit:
            user.save()
        return user


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    stats = {
        'total_courses': Course.objects.count(),
        'total_students': User.objects.filter(user_type='student').count(),
        'total_teachers': User.objects.filter(user_type='teacher').count(),
        'total_announcements': Announcement.objects.count(),
    }
    return render(request, 'home.html', {'stats': stats})


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Votre compte a été créé avec succès.')
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user

    if user.user_type == 'student':
        courses = user.enrolled_courses.select_related('teacher').all()
        assignments = Assignment.objects.filter(course__in=courses).select_related('course').order_by('due_date')
        submissions = {sub.assignment_id: sub for sub in Submission.objects.filter(student=user)}
        announcements = Announcement.objects.filter(Q(is_global=True) | Q(course__in=courses)).select_related('course', 'author').order_by('-created_at')[:5]
        
        avg_grade = Submission.objects.filter(student=user, grade__isnull=False).aggregate(Avg('grade'))['grade__avg']
        stats = {
            'total_courses': courses.count(),
            'total_assignments': assignments.count(),
            'completed_submissions': len(submissions),
            'avg_grade': round(avg_grade, 2) if avg_grade is not None else None,
        }

    elif user.user_type == 'teacher':
        courses = user.taught_courses.all()
        assignments = Assignment.objects.filter(course__in=courses).select_related('course').order_by('due_date')
        submissions = {}
        announcements = Announcement.objects.filter(Q(is_global=True) | Q(course__in=courses)).select_related('course', 'author').order_by('-created_at')[:5]
        
        total_students = User.objects.filter(enrolled_courses__in=courses).distinct().count()
        pending_grades = Submission.objects.filter(assignment__course__in=courses, grade__isnull=True).count()
        stats = {
            'total_courses': courses.count(),
            'total_assignments': assignments.count(),
            'total_students': total_students,
            'pending_grades': pending_grades,
        }

    else:  # admin
        courses = Course.objects.select_related('teacher').all()
        assignments = Assignment.objects.select_related('course').order_by('due_date')
        submissions = {}
        announcements = Announcement.objects.select_related('course', 'author').order_by('-created_at')[:5]
        stats = {
            'total_courses': courses.count(),
            'total_users': User.objects.count(),
            'total_assignments': assignments.count(),
            'pending_users': User.objects.filter(is_validated=False).count(),
        }

    return render(request, 'dashboard.html', {
        'courses': courses,
        'assignments': assignments,
        'submissions': submissions,
        'announcements': announcements,
        'stats': stats,
    })


@login_required
def profile_view(request):
    profile_form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    password_form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Votre profil a été mis à jour avec succès.')
                return redirect('profile')
        elif 'change_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Votre mot de passe a été modifié.')
                return redirect('profile')

    return render(request, 'profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })


@login_required
@user_type_required('admin')
def user_manage_view(request):
    users = User.objects.order_by('-date_joined')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, pk=user_id)
        if action == 'toggle_validation':
            target_user.is_validated = not target_user.is_validated
            target_user.save()
            messages.success(request, f"Statut de validation modifié pour {target_user.username}.")
        elif action == 'change_role':
            new_role = request.POST.get('new_role')
            if new_role in ['student', 'teacher', 'admin']:
                target_user.user_type = new_role
                if new_role == 'admin':
                    target_user.is_staff = True
                else:
                    if not target_user.is_superuser:
                        target_user.is_staff = False
                target_user.save()
                messages.success(request, f"Rôle de {target_user.username} mis à jour : {target_user.get_user_type_display()}.")
        elif action == 'delete_user':
            if target_user == request.user:
                messages.error(request, "Vous ne pouvez pas supprimer votre propre compte administrateur en cours d'utilisation.")
            else:
                username = target_user.username
                target_user.delete()
                messages.success(request, f"L'utilisateur '{username}' a été supprimé avec succès.")
        return redirect('user_manage')

    return render(request, 'user_list.html', {'users': users})


@login_required
@user_type_required('admin')
def user_create_view(request):
    form = AdminUserForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        messages.success(request, f"L'utilisateur '{user.username}' a été créé avec succès.")
        return redirect('user_manage')
    return render(request, 'form.html', {'form': form, 'title': 'Créer un utilisateur', 'submit_label': 'Créer l\'utilisateur'})


@login_required
@user_type_required('admin')
def user_edit_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    form = AdminUserForm(request.POST or None, instance=target_user)
    if form.is_valid():
        form.save()
        messages.success(request, f"Le profil de '{target_user.username}' a été mis à jour.")
        return redirect('user_manage')
    return render(request, 'form.html', {'form': form, 'title': f'Modifier l\'utilisateur : {target_user.username}', 'submit_label': 'Enregistrer les modifications'})


@login_required
@user_type_required('admin')
def user_delete_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte administrateur.")
        return redirect('user_manage')

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"L'utilisateur '{username}' a été supprimé avec succès.")
        return redirect('user_manage')

    return render(request, 'form.html', {
        'title': f'Confirmer la suppression de l\'utilisateur : {target_user.username}',
        'submit_label': 'Oui, supprimer définitivement',
        'confirm_message': True,
    })


@login_required
def search_view(request):
    query = request.GET.get('q', '').strip()
    courses = Course.objects.none()
    assignments = Assignment.objects.none()
    announcements = Announcement.objects.none()

    if query:
        courses = Course.objects.filter(Q(title__icontains=query) | Q(code__icontains=query) | Q(description__icontains=query) | Q(category__icontains=query)).select_related('teacher')
        assignments = Assignment.objects.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(course__code__icontains=query)).select_related('course')
        announcements = Announcement.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)).select_related('author', 'course')

    return render(request, 'search_results.html', {
        'query': query,
        'courses': courses,
        'assignments': assignments,
        'announcements': announcements,
    })


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')


@login_required
def reports_view(request):
    if not request.user.is_teacher_or_admin:
        raise PermissionDenied

    total_students = User.objects.filter(user_type='student').count()
    total_teachers = User.objects.filter(user_type__in=['teacher', 'admin']).count()
    total_courses = Course.objects.count()
    total_assignments = Assignment.objects.count()
    total_submissions = Submission.objects.count()
    graded_submissions = Submission.objects.filter(grade__isnull=False)

    avg_grade_obj = graded_submissions.aggregate(Avg('grade'))
    overall_avg_grade = round(avg_grade_obj['grade__avg'], 2) if avg_grade_obj['grade__avg'] is not None else 0.00

    # Grade Distribution
    grade_excellent = graded_submissions.filter(grade__gte=16).count()
    grade_good = graded_submissions.filter(grade__gte=14, grade__lt=16).count()
    grade_average = graded_submissions.filter(grade__gte=10, grade__lt=14).count()
    grade_poor = graded_submissions.filter(grade__lt=10).count()
    total_graded_count = graded_submissions.count() or 1

    pct_excellent = round((grade_excellent / total_graded_count) * 100, 1)
    pct_good = round((grade_good / total_graded_count) * 100, 1)
    pct_average = round((grade_average / total_graded_count) * 100, 1)
    pct_poor = round((grade_poor / total_graded_count) * 100, 1)

    # Course Stats
    course_stats = Course.objects.annotate(
        students_count=Count('students', distinct=True),
        assignments_count=Count('assignments', distinct=True),
        resources_count=Count('resources', distinct=True),
        avg_course_grade=Avg('assignments__submissions__grade')
    ).select_related('teacher')

    # Filière Stats
    filiere_stats = User.objects.filter(user_type='student').values('filiere').annotate(count=Count('id')).order_by('-count')

    # Chart.js JSON Data
    import json
    course_labels = [f"{cs.code} - {cs.title[:15]}..." if len(cs.title) > 15 else f"{cs.code} - {cs.title}" for cs in course_stats]
    course_averages = [round(float(cs.avg_course_grade), 2) if cs.avg_course_grade is not None else 0.0 for cs in course_stats]

    filiere_labels = [f['filiere'] or 'Non spécifiée' for f in filiere_stats]
    filiere_counts = [f['count'] for f in filiere_stats]

    # Export CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="rapport_statistiques_campus.csv"'
        writer = csv.writer(response)
        writer.writerow(['Rapport Global du Campus Universitaire Codex'])
        writer.writerow([])
        writer.writerow(['Metrique', 'Valeur'])
        writer.writerow(['Etudiants inscrits', total_students])
        writer.writerow(['Enseignants', total_teachers])
        writer.writerow(['Nombre de cours', total_courses])
        writer.writerow(['Missions (Devoirs)', total_assignments])
        writer.writerow(['Travaux rendus (Soumissions)', total_submissions])
        writer.writerow(['Moyenne generale campus (/20)', overall_avg_grade])
        writer.writerow([])
        writer.writerow(['Detail par cours'])
        writer.writerow(['Code', 'Titre du cours', 'Enseignant', 'Etudiants inscrits', 'Devoirs', 'Ressources', 'Moyenne (/20)'])
        for cs in course_stats:
            avg_g = round(cs.avg_course_grade, 2) if cs.avg_course_grade is not None else 'N/A'
            writer.writerow([cs.code, cs.title, cs.teacher.get_full_name() or cs.teacher.username, cs.students_count, cs.assignments_count, cs.resources_count, avg_g])
        return response

    return render(request, 'reports.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'overall_avg_grade': overall_avg_grade,
        'grade_excellent': grade_excellent,
        'grade_good': grade_good,
        'grade_average': grade_average,
        'grade_poor': grade_poor,
        'pct_excellent': pct_excellent,
        'pct_good': pct_good,
        'pct_average': pct_average,
        'pct_poor': pct_poor,
        'course_stats': course_stats,
        'filiere_stats': filiere_stats,
        'course_labels_json': json.dumps(course_labels),
        'course_averages_json': json.dumps(course_averages),
        'filiere_labels_json': json.dumps(filiere_labels),
        'filiere_counts_json': json.dumps(filiere_counts),
    })


@login_required
def notification_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('dashboard')


@login_required
def notifications_mark_all_read_view(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Toutes vos notifications ont été marquées comme lues.')
    return redirect(request.META.get('HTTP_REFERER') or 'dashboard')


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'notifications_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)

def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)



