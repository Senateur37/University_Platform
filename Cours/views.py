import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import FileResponse
from django.db.models import Q
from django import forms

from Comptes.decorateurs import user_type_required
from Comptes.models import User
from .models import Course, CourseResource
from Missions.models import Assignment
from Annonces.models import Announcement


class CourseForm(forms.ModelForm):
    document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.txt,.jpg,.jpeg,.png'}),
        label="Joindre un document depuis votre PC (Optionnel)",
        help_text="Sélectionnez un fichier sur votre ordinateur (PDF, Word, PPT, ZIP, etc.)"
    )

    class Meta:
        model = Course
        fields = ('title', 'code', 'category', 'licence', 'description', 'teacher')
        labels = {
            'title': 'Titre du cours',
            'code': 'Code du cours (ex: INFO101)',
            'category': 'Filière / Catégorie',
            'licence': 'Licence concernée (Niveau requis)',
            'description': 'Description du cours',
            'teacher': 'Enseignant responsable',
        }
        help_texts = {
            'licence': 'Indiquez quelle Licence ce cours concerne (Licence 1, Licence 2, Licence 3 ou Toutes les Licences).',
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = CourseResource
        fields = ('title', 'file', 'description')
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.txt,.jpg,.jpeg,.png'}),
        }
        labels = {
            'title': 'Titre du document / ressource',
            'file': 'Sélectionner le fichier sur votre PC',
            'description': 'Description courte (optionnelle)',
        }


def course_list(request):
    category = request.GET.get('cat', '').strip()
    query = request.GET.get('q', '').strip()
    selected_licence = request.GET.get('licence', '').strip()
    
    try:
        courses = Course.objects.select_related('teacher').all()
        if category:
            courses = courses.filter(category__iexact=category)
        if selected_licence:
            if selected_licence == 'ALL':
                courses = courses.filter(licence='ALL')
            else:
                courses = courses.filter(Q(licence=selected_licence) | Q(licence='ALL'))
        if query:
            courses = courses.filter(Q(title__icontains=query) | Q(code__icontains=query) | Q(description__icontains=query))
        courses = list(courses)
        for c in courses:
            c.has_user_access = c.user_has_access(request.user) if request.user.is_authenticated else False
        categories = [c for c in Course.objects.values_list('category', flat=True).distinct() if c]
    except Exception as e:
        courses = []
        categories = []

    return render(request, 'courses/list.html', {
        'courses': courses,
        'categories': categories,
        'selected_category': category,
        'selected_licence': selected_licence,
        'licence_choices': Course.LICENCE_CHOICES,
        'search_query': query,
    })


def course_detail(request, pk):
    course = get_object_or_404(Course.objects.select_related('teacher').prefetch_related('resources', 'students'), pk=pk)
    assignments = course.assignments.order_by('due_date')
    announcements = course.announcements.select_related('author').order_by('-created_at')
    
    is_enrolled = False
    has_access = course.user_has_access(request.user) if request.user.is_authenticated else False

    if request.user.is_authenticated and request.user.user_type == 'student':
        is_enrolled = course.students.filter(pk=request.user.pk).exists()

    is_owner = request.user.is_authenticated and (request.user == course.teacher or request.user.user_type == 'admin')

    return render(request, 'courses/detail.html', {
        'course': course,
        'assignments': assignments,
        'announcements': announcements,
        'is_enrolled': is_enrolled,
        'has_access': has_access,
        'is_owner': is_owner,
    })


@login_required
@user_type_required('teacher', 'admin')
def course_create(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.user.is_superuser or request.user.is_staff or request.user.user_type == 'admin':
        form.fields['teacher'].queryset = User.objects.filter(
            Q(user_type__in=['teacher', 'admin']) | Q(is_staff=True) | Q(is_superuser=True)
        ).distinct()
        if not request.POST:
            form.initial['teacher'] = request.user
    else:
        if 'teacher' in form.fields:
            del form.fields['teacher']

    if form.is_valid():
        course = form.save(commit=False)
        if not getattr(course, 'teacher_id', None):
            course.teacher = request.user
        course.save()

        doc = form.cleaned_data.get('document')
        if doc:
            CourseResource.objects.create(
                course=course,
                title=doc.name,
                file=doc,
                description="Document d'accompagnement du cours"
            )

        messages.success(request, 'Cours créé avec succès.')
        return redirect('course_detail', course.pk)
    return render(request, 'form.html', {'form': form, 'title': 'Créer un nouveau cours', 'submit_label': 'Créer'})


@login_required
@user_type_required('teacher', 'admin')
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user.user_type != 'admin' and not request.user.is_superuser and course.teacher != request.user:
        messages.error(request, "Accès refusé : vous n'êtes pas le responsable de ce cours.")
        return redirect('course_detail', pk=course.pk)

    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.user.is_superuser or request.user.is_staff or request.user.user_type == 'admin':
        form.fields['teacher'].queryset = User.objects.filter(
            Q(user_type__in=['teacher', 'admin']) | Q(is_staff=True) | Q(is_superuser=True)
        ).distinct()
    else:
        if 'teacher' in form.fields:
            del form.fields['teacher']

    if form.is_valid():
        form.save()

        doc = form.cleaned_data.get('document')
        if doc:
            CourseResource.objects.create(
                course=course,
                title=doc.name,
                file=doc,
                description="Document d'accompagnement du cours"
            )

        messages.success(request, 'Cours mis à jour avec succès.')
        return redirect('course_detail', course.pk)
    return render(request, 'form.html', {'form': form, 'title': f'Modifier : {course.title}', 'submit_label': 'Enregistrer'})


@login_required
@user_type_required('teacher', 'admin')
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user.user_type != 'admin' and not request.user.is_superuser and course.teacher != request.user:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à supprimer ce cours.")
        return redirect('course_list')

    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f'Le cours "{title}" a été supprimé.')
        return redirect('course_list')

    return render(request, 'form.html', {
        'title': f'Confirmer la suppression du cours : {course.title}',
        'submit_label': 'Oui, supprimer définitivement',
        'confirm_message': True,
    })


@login_required
@user_type_required('student')
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if not course.user_has_access(request.user):
        messages.error(
            request,
            f"Accès refusé : Ce cours est réservé aux étudiants de {course.get_licence_display()}. "
            f"Votre niveau actuel ({request.user.get_licence_display() or 'non spécifié'}) ne vous permet pas de vous y inscrire."
        )
        return redirect('course_detail', pk=course.pk)
    course.students.add(request.user)
    messages.success(request, f'Vous êtes maintenant inscrit au cours "{course.title}".')
    return redirect('course_detail', course.pk)


@login_required
@user_type_required('student')
def unenroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    course.students.remove(request.user)
    messages.info(request, f'Vous vous êtes désinscrit du cours "{course.title}".')
    return redirect('course_detail', course.pk)


@login_required
@user_type_required('teacher', 'admin')
def resource_create(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user.user_type != 'admin' and not request.user.is_superuser and course.teacher != request.user:
        messages.error(request, "Accès refusé : seul le responsable du cours ou un administrateur peut ajouter une ressource.")
        return redirect('course_detail', pk=course.pk)

    form = ResourceForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        resource = form.save(commit=False)
        resource.course = course
        resource.save()
        messages.success(request, 'Ressource ajoutée avec succès.')
        return redirect('course_detail', course.pk)
    return render(request, 'form.html', {'form': form, 'title': f'Ajouter une ressource à {course.code}', 'submit_label': 'Téléverser'})


@login_required
@user_type_required('teacher', 'admin')
def resource_delete(request, pk, resource_pk):
    course = get_object_or_404(Course, pk=pk)
    if request.user.user_type != 'admin' and not request.user.is_superuser and course.teacher != request.user:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à supprimer cette ressource.")
        return redirect('course_detail', pk=course.pk)

    resource = get_object_or_404(CourseResource, pk=resource_pk, course=course)
    resource.delete()
    messages.success(request, 'Ressource supprimée.')
    return redirect('course_detail', course.pk)


@login_required
def resource_download(request, pk, resource_pk):
    course = get_object_or_404(Course, pk=pk)
    resource = get_object_or_404(CourseResource, pk=resource_pk, course=course)

    if request.user.user_type == 'student' and not course.user_has_access(request.user):
        messages.error(
            request,
            f"Accès refusé : Le téléchargement des documents de ce cours est réservé aux étudiants de {course.get_licence_display()}."
        )
        return redirect('course_detail', pk=pk)

    if not resource.file:
        messages.error(request, "Aucun fichier disponible pour ce document.")
        return redirect('course_detail', pk=pk)

    try:
        filename = os.path.basename(resource.file.name)
        return FileResponse(resource.file.open('rb'), as_attachment=True, filename=filename)
    except (FileNotFoundError, ValueError):
        messages.error(request, "Le fichier est introuvable sur le serveur.")
        return redirect('course_detail', pk=pk)


