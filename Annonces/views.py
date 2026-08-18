from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django import forms

from Comptes.decorateurs import user_type_required
from Cours.models import Course
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('course', 'title', 'content', 'is_global')
        labels = {
            'course': 'Cours associé (Laisser vide pour une annonce générale du campus)',
            'title': "Titre de l'annonce",
            'content': 'Contenu de la publication',
            'is_global': 'Rendre visible par tout le campus (Annonce globale)',
        }


def announcement_list(request):
    announcements = Announcement.objects.select_related('course', 'author').order_by('-created_at')
    return render(request, 'announcements/list.html', {'announcements': announcements})


def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement.objects.select_related('course', 'author'), pk=pk)
    is_author = request.user.is_authenticated and (request.user == announcement.author or request.user.user_type == 'admin')
    return render(request, 'announcements/detail.html', {
        'announcement': announcement,
        'is_author': is_author,
    })


@login_required
@user_type_required('teacher', 'admin')
def announcement_create(request):
    form = AnnouncementForm(request.POST or None)
    if request.user.user_type == 'teacher':
        form.fields['course'].queryset = Course.objects.filter(teacher=request.user)

    if form.is_valid():
        announcement = form.save(commit=False)
        announcement.author = request.user
        announcement.save()
        messages.success(request, 'Annonce publiée avec succès.')
        return redirect('announcement_list')
    return render(request, 'form.html', {'form': form, 'title': 'Publier une annonce', 'submit_label': 'Publier'})


@login_required
@user_type_required('teacher', 'admin')
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    form = AnnouncementForm(request.POST or None, instance=announcement)
    if request.user.user_type == 'teacher':
        form.fields['course'].queryset = Course.objects.filter(teacher=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, 'Annonce mise à jour.')
        return redirect('announcement_detail', announcement.pk)
    return render(request, 'form.html', {'form': form, 'title': f'Modifier : {announcement.title}', 'submit_label': 'Enregistrer'})


@login_required
@user_type_required('teacher', 'admin')
def announcement_delete(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    if request.method == 'POST':
        title = announcement.title
        announcement.delete()
        messages.success(request, f'L\'annonce "{title}" a été supprimée.')
        return redirect('announcement_list')

    return render(request, 'form.html', {
        'title': f'Confirmer la suppression de l\'annonce : {announcement.title}',
        'submit_label': 'Oui, supprimer définitivement',
        'confirm_message': True,
    })

