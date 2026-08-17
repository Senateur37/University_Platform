from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from Comptes.decorateurs import user_type_required
from Cours.models import Course
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
	class Meta:
		model = Announcement
		fields = ('course', 'title', 'content', 'is_global')


def announcement_list(request):
	return render(request, 'announcements/list.html', {'announcements': Announcement.objects.select_related('course', 'author').order_by('-created_at')})


@login_required
@user_type_required('teacher', 'admin')
def announcement_create(request):
	form = AnnouncementForm(request.POST or None)
	if form.is_valid():
		announcement = form.save(commit=False)
		announcement.author = request.user
		announcement.save()
		return redirect('announcement_list')
	return render(request, 'form.html', {'form': form, 'title': 'Publier une annonce', 'submit_label': 'Publier'})
