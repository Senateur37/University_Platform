from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django import forms

from Comptes.decorateurs import user_type_required
from .models import Course, CourseResource


class CourseForm(forms.ModelForm):
	class Meta:
		model = Course
		fields = ('title', 'code', 'description')


class ResourceForm(forms.ModelForm):
	class Meta:
		model = CourseResource
		fields = ('title', 'file', 'description')


def course_list(request):
	return render(request, 'courses/list.html', {'courses': Course.objects.select_related('teacher').all()})


def course_detail(request, pk):
	return render(request, 'courses/detail.html', {'course': get_object_or_404(Course, pk=pk)})


@login_required
@user_type_required('teacher', 'admin')
def course_create(request):
	form = CourseForm(request.POST or None)
	if form.is_valid():
		course = form.save(commit=False)
		course.teacher = request.user
		course.save()
		messages.success(request, 'Cours créé avec succès.')
		return redirect('course_detail', course.pk)
	return render(request, 'form.html', {'form': form, 'title': 'Créer un cours', 'submit_label': 'Créer'})


@login_required
@user_type_required('student')
def enroll(request, pk):
	course = get_object_or_404(Course, pk=pk)
	course.students.add(request.user)
	messages.success(request, 'Vous êtes inscrit à ce cours.')
	return redirect('course_detail', course.pk)


@login_required
@user_type_required('teacher', 'admin')
def resource_create(request, pk):
	course = get_object_or_404(Course, pk=pk)
	form = ResourceForm(request.POST or None, request.FILES or None)
	if form.is_valid():
		resource = form.save(commit=False)
		resource.course = course
		resource.save()
		return redirect('course_detail', course.pk)
	return render(request, 'form.html', {'form': form, 'title': 'Ajouter une ressource', 'submit_label': 'Téléverser'})
