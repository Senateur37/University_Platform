from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django import forms

from Comptes.decorateurs import user_type_required
from Cours.models import Course
from .models import Assignment, Submission


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ('course', 'title', 'description', 'max_points', 'attachment', 'due_date')
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'attachment': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.txt,.jpg,.jpeg,.png'}),
        }
        labels = {
            'course': 'Cours associé',
            'title': 'Titre de la mission',
            'description': 'Consignes / Description',
            'max_points': 'Note maximale (ex: 20)',
            'attachment': 'Sujet / Pièce jointe depuis votre PC (Optionnel)',
            'due_date': 'Date et heure limite',
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('file',)
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.rar,.txt,.jpg,.jpeg,.png'}),
        }
        labels = {
            'file': 'Sélectionner votre travail depuis votre PC (PDF, ZIP, Doc...)',
        }


class GradeForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('grade', 'feedback')
        labels = {
            'grade': 'Note attribuée',
            'feedback': 'Commentaires et conseils',
        }


def assignment_list(request):
    assignments = Assignment.objects.select_related('course', 'course__teacher').order_by('due_date')
    submissions_dict = {}

    if request.user.is_authenticated:
        if request.user.user_type == 'student':
            user_subs = Submission.objects.filter(student=request.user)
            submissions_dict = {sub.assignment_id: sub for sub in user_subs}
        elif request.user.user_type in ['teacher', 'admin']:
            pass

    return render(request, 'missions/list.html', {
        'assignments': assignments,
        'submissions_dict': submissions_dict,
        'now': timezone.now(),
    })


@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related('course', 'course__teacher'), pk=pk)
    submission = None
    if request.user.user_type == 'student':
        submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    
    is_teacher_owner = (request.user == assignment.course.teacher or request.user.user_type == 'admin')

    return render(request, 'missions/detail.html', {
        'assignment': assignment,
        'submission': submission,
        'is_teacher_owner': is_teacher_owner,
        'now': timezone.now(),
    })


@login_required
@user_type_required('teacher', 'admin')
def assignment_create(request):
    form = AssignmentForm(request.POST or None, request.FILES or None)
    if request.user.user_type == 'teacher':
        form.fields['course'].queryset = Course.objects.filter(teacher=request.user)
        
    if form.is_valid():
        assignment = form.save()

        # Notify enrolled students
        from Comptes.models import Notification
        from django.urls import reverse
        link = reverse('assignment_detail', args=[assignment.pk])
        recipients = assignment.course.students.exclude(pk=request.user.pk)
        due_str = assignment.due_date.strftime('%d/%m/%Y') if assignment.due_date else ''
        notifs = [
            Notification(
                recipient=u,
                notification_type='assignment',
                title=f"🎯 Nouvelle mission ({assignment.course.code}) : {assignment.title}",
                message=f"À rendre avant le {due_str}",
                link=link
            )
            for u in recipients
        ]
        if notifs:
            Notification.objects.bulk_create(notifs)

        messages.success(request, 'La mission a été créée avec succès.')
        return redirect('assignment_detail', assignment.pk)
    return render(request, 'form.html', {'form': form, 'title': 'Créer une nouvelle mission', 'submit_label': 'Créer la mission'})


@login_required
@user_type_required('teacher', 'admin')
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    form = AssignmentForm(request.POST or None, request.FILES or None, instance=assignment)
    if request.user.user_type == 'teacher':
        form.fields['course'].queryset = Course.objects.filter(teacher=request.user)

    if form.is_valid():
        form.save()
        messages.success(request, 'La mission a été mise à jour.')
        return redirect('assignment_detail', assignment.pk)
    return render(request, 'form.html', {'form': form, 'title': f'Modifier : {assignment.title}', 'submit_label': 'Enregistrer'})


@login_required
@user_type_required('teacher', 'admin')
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    if request.method == 'POST':
        title = assignment.title
        assignment.delete()
        messages.success(request, f'La mission "{title}" a été supprimée.')
        return redirect('assignment_list')

    return render(request, 'form.html', {
        'title': f'Confirmer la suppression de la mission : {assignment.title}',
        'submit_label': 'Oui, supprimer définitivement',
        'confirm_message': True,
    })


@login_required
@user_type_required('student')
def submit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    existing_sub = Submission.objects.filter(assignment=assignment, student=request.user).first()
    
    form = SubmissionForm(request.POST or None, request.FILES or None, instance=existing_sub)
    if form.is_valid():
        submission = form.save(commit=False)
        submission.assignment = assignment
        submission.student = request.user
        submission.save()
        messages.success(request, 'Votre travail a été rendu avec succès.')
        return redirect('assignment_detail', assignment.pk)
    
    return render(request, 'form.html', {
        'form': form,
        'title': f'Rendre la mission : {assignment.title}',
        'submit_label': 'Téléverser et Soumettre',
    })


@login_required
@user_type_required('teacher', 'admin')
def assignment_submissions(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related('course'), pk=pk)
    if request.user != assignment.course.teacher and request.user.user_type != 'admin':
        messages.error(request, "Action non autorisée.")
        return redirect('assignment_list')

    submissions = Submission.objects.filter(assignment=assignment).select_related('student').order_by('-submitted_at')
    
    return render(request, 'missions/submissions.html', {
        'assignment': assignment,
        'submissions': submissions,
    })


@login_required
@user_type_required('teacher', 'admin')
def grade_submission(request, pk, submission_pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    submission = get_object_or_404(Submission.objects.select_related('student'), pk=submission_pk, assignment=assignment)
    
    if request.user != assignment.course.teacher and request.user.user_type != 'admin':
        messages.error(request, "Action non autorisée.")
        return redirect('assignment_submissions', assignment.pk)

    form = GradeForm(request.POST or None, instance=submission)
    if form.is_valid():
        form.save()

        # Notify student of their grade
        from Comptes.models import Notification
        from django.urls import reverse
        link = reverse('assignment_detail', args=[assignment.pk])
        Notification.objects.create(
            recipient=submission.student,
            notification_type='grade',
            title=f"⭐ Note attribuée : {assignment.title}",
            message=f"Vous avez obtenu {submission.grade}/{assignment.max_points}.",
            link=link
        )

        messages.success(request, f'Note attribuée à {submission.student.get_full_name() or submission.student.username}.')
        return redirect('assignment_submissions', assignment.pk)

    return render(request, 'form.html', {
        'form': form,
        'title': f'Évaluer la copie de {submission.student.get_full_name() or submission.student.username} ({assignment.title})',
        'submit_label': 'Enregistrer la note',
    })

