from django.test import TestCase
from django.urls import reverse

from Cours.models import Course

from .models import User


class PlatformFlowTests(TestCase):
	def setUp(self):
		self.teacher = User.objects.create_user(username='teacher', password='pass12345', user_type='teacher')
		self.student = User.objects.create_user(username='student', password='pass12345', user_type='student')
		self.course = Course.objects.create(title='Python', code='PY101', teacher=self.teacher)

	def test_home_and_course_list_are_public(self):
		self.assertEqual(self.client.get(reverse('home')).status_code, 200)
		response = self.client.get(reverse('course_list'))
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Python')

	def test_student_can_enroll(self):
		self.client.force_login(self.student)
		response = self.client.get(reverse('enroll', args=[self.course.pk]))
		self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
		self.assertTrue(self.course.students.filter(pk=self.student.pk).exists())

	def test_student_cannot_create_course(self):
		self.client.force_login(self.student)
		self.assertEqual(self.client.get(reverse('course_create')).status_code, 403)

	def test_dashboard_is_available_at_dashboard_url(self):
		self.client.force_login(self.student)
		response = self.client.get('/dashboard/')
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'dashboard.html')

	def test_registration_creates_student_account(self):
		response = self.client.post(reverse('register'), {
			'username': 'newstudent', 'email': 'new@example.com',
			'first_name': 'New', 'last_name': 'Student', 'user_type': 'student',
			'password': 'pass12345', 'password_confirmation': 'pass12345',
		})
		self.assertRedirects(response, reverse('dashboard'))
		self.assertTrue(User.objects.filter(username='newstudent').exists())
