from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from django import forms

from Comptes.decorateurs import user_type_required
from Comptes.models import User, Notification
from Cours.models import Course
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('course', 'licence', 'title', 'content', 'is_global')
        labels = {
            'course': 'Cours associé (Optionnel - laisser vide pour une annonce générale du campus)',
            'licence': 'Licence concernée',
            'title': "Titre de l'annonce",
            'content': 'Contenu de la publication',
            'is_global': 'Rendre visible par tout le campus (Annonce globale)',
        }
        help_texts = {
            'licence': 'Choisissez la Licence concernée (L1, L2, L3 ou Toutes les Licences pour tout le campus).',
        }


def announcement_list(request):
    selected_licence = request.GET.get('licence', '').strip()
    user = request.user

    try:
        queryset = Announcement.objects.select_related('course', 'author').order_by('-created_at')

        # Si l'utilisateur est un étudiant, filtrer les annonces pour sa Licence ou Tout le campus
        if user.is_authenticated and user.user_type == 'student':
            student_filter = Q(licence='ALL') | Q(licence='') | Q(licence__isnull=True)
            if user.licence:
                student_filter |= Q(licence=user.licence)
            if hasattr(user, 'enrolled_courses'):
                student_filter |= Q(course__in=user.enrolled_courses.all())
            queryset = queryset.filter(student_filter)

        if selected_licence:
            if selected_licence == 'ALL':
                queryset = queryset.filter(licence='ALL')
            else:
                queryset = queryset.filter(licence=selected_licence)

        announcements = list(queryset)
    except Exception:
        announcements = []

    return render(request, 'announcements/list.html', {
        'announcements': announcements,
        'selected_licence': selected_licence,
        'licence_choices': Announcement.LICENCE_CHOICES,
    })


def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement.objects.select_related('course', 'author'), pk=pk)
    is_author = request.user.is_authenticated and (request.user == announcement.author or request.user.user_type == 'admin')
    
    # Vérifier la correspondance de licence pour information de l'étudiant
    is_student_match = True
    if request.user.is_authenticated and request.user.user_type == 'student':
        if announcement.licence and announcement.licence != 'ALL' and request.user.licence:
            is_student_match = (request.user.licence == announcement.licence)

    return render(request, 'announcements/detail.html', {
        'announcement': announcement,
        'is_author': is_author,
        'is_student_match': is_student_match,
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

        # Envoi ciblé des notifications aux étudiants selon la Licence
        from django.urls import reverse
        link = reverse('announcement_detail', args=[announcement.pk])

        if announcement.course:
            recipients = announcement.course.students.exclude(pk=request.user.pk)
            code_text = f" ({announcement.course.code})"
        else:
            recipients = User.objects.filter(user_type='student').exclude(pk=request.user.pk)
            if announcement.licence and announcement.licence != 'ALL':
                recipients = recipients.filter(licence=announcement.licence)
                code_text = f" ({announcement.licence})"
            else:
                code_text = " (Campus)"

        notifs = [
            Notification(
                recipient=u,
                notification_type='announcement',
                title=f"📢 Nouvelle annonce{code_text} : {announcement.title}",
                message=announcement.content[:100],
                link=link
            )
            for u in recipients
        ]
        if notifs:
            Notification.objects.bulk_create(notifs)

        messages.success(request, 'Annonce publiée avec succès.')
        return redirect('announcement_list')
    return render(request, 'form.html', {'form': form, 'title': 'Publier une annonce', 'submit_label': 'Publier'})


@login_required
@user_type_required('teacher', 'admin')
def announcement_edit(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.user.user_type != 'admin' and not request.user.is_superuser and announcement.author != request.user:
        messages.error(request, "Accès refusé : vous n'êtes pas l'auteur de cette annonce.")
        return redirect('announcement_detail', pk=announcement.pk)

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
    if request.user.user_type != 'admin' and not request.user.is_superuser and announcement.author != request.user:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à supprimer cette annonce.")
        return redirect('announcement_list')

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

