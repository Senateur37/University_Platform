from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from Comptes.models import User
from Cours.models import Course, CourseResource
from Missions.models import Assignment, Submission
from Annonces.models import Announcement


class ComprehensivePlatformTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin_user', password='password123', user_type='admin', is_staff=True)
        self.teacher = User.objects.create_user(username='teacher_user', password='password123', user_type='teacher')
        self.student = User.objects.create_user(username='student_user', password='password123', user_type='student')
        
        self.course = Course.objects.create(
            title='Algorithmique',
            code='ALG101',
            category='Informatique',
            description='Bases de l-algorithmique',
            teacher=self.teacher,
        )
        self.assignment = Assignment.objects.create(
            course=self.course,
            title='Devoir 1',
            description='Faire les exercices 1 et 2',
            max_points=20.00,
            due_date=timezone.now() + timedelta(days=5),
        )
        self.announcement = Announcement.objects.create(
            title='Bienvenue',
            content='Contenu de bienvenue',
            author=self.admin,
            is_global=True,
        )

    def test_home_and_course_list_access(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Algorithmique')

    def test_student_enrollment_and_unenrollment(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('enroll', args=[self.course.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
        self.assertTrue(self.course.students.filter(pk=self.student.pk).exists())

        # Test unenroll
        response = self.client.get(reverse('unenroll', args=[self.course.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[self.course.pk]))
        self.assertFalse(self.course.students.filter(pk=self.student.pk).exists())

    def test_teacher_course_crud(self):
        self.client.force_login(self.teacher)
        # Create
        response = self.client.post(reverse('course_create'), {
            'title': 'Nouveau Cours',
            'code': 'NC101',
            'category': 'Informatique',
            'description': 'Description du cours',
        })
        new_course = Course.objects.get(code='NC101')
        self.assertRedirects(response, reverse('course_detail', args=[new_course.pk]))

        # Edit
        response = self.client.post(reverse('course_edit', args=[new_course.pk]), {
            'title': 'Nouveau Cours Modifie',
            'code': 'NC101',
            'category': 'Informatique',
            'description': 'Modifie',
        })
        self.assertRedirects(response, reverse('course_detail', args=[new_course.pk]))
        new_course.refresh_from_db()
        self.assertEqual(new_course.title, 'Nouveau Cours Modifie')

        # Delete
        response = self.client.post(reverse('course_delete', args=[new_course.pk]))
        self.assertRedirects(response, reverse('course_list'))
        self.assertFalse(Course.objects.filter(pk=new_course.pk).exists())

    def test_assignment_submission_and_grading(self):
        # Student submits
        self.client.force_login(self.student)
        self.course.students.add(self.student)
        
        sub = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            file='test.pdf',
        )

        # Teacher grades submission
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('grade_submission', args=[self.assignment.pk, sub.pk]), {
            'grade': '18.00',
            'feedback': 'Très bon travail',
        })
        self.assertRedirects(response, reverse('assignment_submissions', args=[self.assignment.pk]))
        sub.refresh_from_db()
        self.assertEqual(sub.grade, 18.00)
        self.assertEqual(sub.feedback, 'Très bon travail')

    def test_global_search(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('search') + '?q=Algorithmique')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Algorithmique')

    def test_user_profile_edit(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('profile'), {
            'update_profile': '1',
            'first_name': 'Alice',
            'last_name': 'Martin',
            'email': 'alice.martin@univ.fr',
            'filiere': 'Master Data',
            'bio': 'Passionnee d-IA',
        })
        self.assertRedirects(response, reverse('profile'))
        self.student.refresh_from_db()
        self.assertEqual(self.student.first_name, 'Alice')
        self.assertEqual(self.student.filiere, 'Master Data')

    def test_admin_user_management(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('user_manage'))
        self.assertEqual(response.status_code, 200)

        # Toggle validation
        response = self.client.post(reverse('user_manage'), {
            'user_id': self.student.pk,
            'action': 'toggle_validation',
        })
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_validated)

    def test_only_admin_can_access_user_manage(self):
        # Admin gets 200
        self.client.force_login(self.admin)
        response = self.client.get(reverse('user_manage'))
        self.assertEqual(response.status_code, 200)

        # Teacher gets 403 Forbidden
        self.client.force_login(self.teacher)
        response = self.client.get(reverse('user_manage'))
        self.assertEqual(response.status_code, 403)

        # Student gets 403 Forbidden
        self.client.force_login(self.student)
        response = self.client.get(reverse('user_manage'))
        self.assertEqual(response.status_code, 403)

    def test_forum_topic_creation_and_reply(self):
        from Forum.models import ForumTopic, ForumPost, ForumCategory
        cat = ForumCategory.objects.create(name="Entraide", slug="entraide")
        
        # Student creates topic
        self.client.force_login(self.student)
        response = self.client.post(reverse('topic_create'), {
            'title': 'Question sur les fonctions',
            'category': cat.pk,
            'content': 'Comment utiliser def en Python ?',
        })
        topic = ForumTopic.objects.get(title='Question sur les fonctions')
        self.assertRedirects(response, reverse('topic_detail', args=[topic.pk]))

        # Teacher replies to topic
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('post_create', args=[topic.pk]), {
            'content': 'On utilise def nom_fonction(): ...',
        })
        self.assertRedirects(response, reverse('topic_detail', args=[topic.pk]))
        self.assertTrue(ForumPost.objects.filter(topic=topic, author=self.teacher).exists())

    def test_reports_view_and_csv_export(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rapports')

        # CSV export
        response_csv = self.client.get(reverse('reports') + '?export=csv')
        self.assertEqual(response_csv.status_code, 200)
        self.assertTrue(response_csv['Content-Type'].startswith('text/csv'))
        self.assertIn('Rapport Global', response_csv.content.decode('utf-8-sig'))

    def test_resource_download_view(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from Cours.models import CourseResource

        file = SimpleUploadedFile("test_document.txt", b"Contenu du cours de test", content_type="text/plain")
        resource = CourseResource.objects.create(
            course=self.course,
            title="Support de cours",
            file=file
        )

        self.client.force_login(self.student)
        response = self.client.get(reverse('resource_download', args=[self.course.pk, resource.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

