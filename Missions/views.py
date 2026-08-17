from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django import forms

from Comptes.decorateurs import user_type_required
from Cours.models import Course
from .models import Assignment, Submission


class AssignmentForm(forms.ModelForm):
	class Meta:
		model = Assignment
		fields = ('course', 'title', 'description', 'due_date')


class SubmissionForm(forms.ModelForm):
	class Meta:
		model = Submission
		fields = ('file',)


def assignment_list(request):
	assignments = Assignment.objects.select_related('course').order_by('due_date')
	return render(request, 'missions/list.html', {'assignments': assignments})


@login_required
@user_type_required('teacher', 'admin')
def assignment_create(request):
	form = AssignmentForm(request.POST or None)
	if form.is_valid():
		assignment = form.save()
		return redirect('assignment_list')
	return render(request, 'form.html', {'form': form, 'title': 'Créer une mission', 'submit_label': 'Créer'})


@login_required
@user_type_required('student')
def submit_assignment(request, pk):
	assignment = get_object_or_404(Assignment, pk=pk)
	form = SubmissionForm(request.POST or None, request.FILES or None, instance=Submission.objects.filter(assignment=assignment, student=request.user).first())
	if form.is_valid():
		submission = form.save(commit=False)
		submission.assignment = assignment
		submission.student = request.user
		submission.save()
		return redirect('assignment_list')
	return render(request, 'form.html', {'form': form, 'title': f'Rendre: {assignment.title}', 'submit_label': 'Soumettre'})
