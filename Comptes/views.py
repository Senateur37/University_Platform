from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django import forms

from .models import User
from Missions.models import Assignment


class RegistrationForm(forms.ModelForm):
	password = forms.CharField(widget=forms.PasswordInput)
	password_confirmation = forms.CharField(widget=forms.PasswordInput)

	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'user_type')

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


def home(request):
	return render(request, 'home.html')


def register(request):
	form = RegistrationForm(request.POST or None)
	if form.is_valid():
		user = form.save()
		login(request, user)
		messages.success(request, 'Votre compte a été créé.')
		return redirect('dashboard')
	return render(request, 'form.html', {'form': form, 'title': 'Créer un compte', 'submit_label': 'S inscrire'})


@login_required
def dashboard(request):
	return render(request, 'dashboard.html', {
		'courses': request.user.enrolled_courses.all() if request.user.user_type == 'student' else request.user.taught_courses.all(),
		'assignments': Assignment.objects.filter(course__students=request.user) if request.user.user_type == 'student' else Assignment.objects.filter(course__teacher=request.user),
	})
