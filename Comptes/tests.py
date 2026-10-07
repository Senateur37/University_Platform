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

    def test_notifications_system(self):
        from Comptes.models import Notification

        # Enroll student in course
        self.course.students.add(self.student)

        # Create an announcement to trigger notification
        self.client.force_login(self.teacher)
        self.client.post(reverse('announcement_create'), {
            'title': 'Annonce test notification',
            'content': 'Contenu important',
            'course': self.course.pk
        })

        # Verify student receives notification
        notif = Notification.objects.filter(recipient=self.student).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, 'announcement')
        self.assertFalse(notif.is_read)

        # Mark notification as read
        self.client.force_login(self.student)
        response = self.client.get(reverse('notification_read', args=[notif.pk]))
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

        # Mark all read
        Notification.objects.create(recipient=self.student, title="Autre notif", notification_type="forum", is_read=False)
        self.client.get(reverse('notifications_mark_all_read'))
        unread_count = Notification.objects.filter(recipient=self.student, is_read=False).count()
        self.assertEqual(unread_count, 0)

    def test_security_headers(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-XSS-Protection'), '1; mode=block')
        self.assertIn('Content-Security-Policy', response.headers)
        self.assertIn('Permissions-Policy', response.headers)

    def test_login_rate_limiting(self):
        # Perform 5 failed login attempts
        for i in range(5):
            response = self.client.post(reverse('login'), {'username': 'wrong_user', 'password': 'wrong_password'})
            self.assertEqual(response.status_code, 200)

        # 6th attempt should be blocked with HTTP 429
        response_blocked = self.client.post(reverse('login'), {'username': 'wrong_user', 'password': 'wrong_password'})
        self.assertEqual(response_blocked.status_code, 429)
        self.assertIn('Accès temporairement bloqué', response_blocked.content.decode('utf-8'))

    def test_dangerous_file_upload_blocking(self):
        from django.core.exceptions import ValidationError
        from Codex.validators import validate_secure_file_extension, validate_avatar_image
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Executable file test
        bad_file = SimpleUploadedFile("malicious.php", b"<?php echo 'hacked'; ?>", content_type="application/x-php")
        with self.assertRaises(ValidationError):
            validate_secure_file_extension(bad_file)

        bad_exe = SimpleUploadedFile("virus.exe", b"MZ...", content_type="application/x-msdownload")
        with self.assertRaises(ValidationError):
            validate_secure_file_extension(bad_exe)

        # Non-image avatar test
        bad_avatar = SimpleUploadedFile("shell.py", b"import os; os.system('ls')", content_type="text/x-python")
        with self.assertRaises(ValidationError):
            validate_avatar_image(bad_avatar)

    def test_anti_reverse_engineering_headers(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.headers.get('Server'), 'Protected-Campus-Server')
        self.assertNotIn('X-Powered-By', response.headers)
        self.assertNotIn('X-Django-Version', response.headers)

    def test_custom_error_pages(self):
        response_404 = self.client.get('/route-qui-n-existe-pas-12345/')
        self.assertEqual(response_404.status_code, 404)
        self.assertIn('Page non trouvée', response_404.content.decode('utf-8'))

    def test_weak_password_registration_rejected(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser123',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'filiere': 'Info',
            'user_type': 'student',
            'bio': 'Test bio',
            'password': '123',
            'password_confirmation': '123'
        })
        # Should stay on page (200 with form errors) instead of redirecting
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser123').exists())

    def test_idor_protection_course_and_assignment_edit(self):
        other_teacher = User.objects.create_user(username='other_teacher', password='password123', user_type='teacher')
        self.client.force_login(other_teacher)

        # Attempt to edit another teacher's course
        response_course = self.client.post(reverse('course_edit', args=[self.course.pk]), {
            'title': 'Hacked Title',
            'code': 'ALG101',
            'category': 'Informatique',
            'description': 'Hacked description',
        })
        self.course.refresh_from_db()
        self.assertNotEqual(self.course.title, 'Hacked Title')

        # Attempt to edit another teacher's assignment
        response_assign = self.client.post(reverse('assignment_edit', args=[self.assignment.pk]), {
            'course': self.course.pk,
            'title': 'Hacked Assignment',
            'description': 'Hacked',
            'max_points': 20.00,
            'due_date': timezone.now() + timedelta(days=2),
        })
        self.assignment.refresh_from_db()
        self.assertNotEqual(self.assignment.title, 'Hacked Assignment')

    def test_non_enrolled_student_cannot_submit_assignment(self):
        self.client.force_login(self.student)
        from django.core.files.uploadedfile import SimpleUploadedFile
        test_file = SimpleUploadedFile("devoir.pdf", b"%PDF-1.4 test", content_type="application/pdf")

        # Student is not enrolled, submission should be rejected
        response = self.client.post(reverse('submit_assignment', args=[self.assignment.pk]), {
            'file': test_file
        })
        self.assertFalse(Submission.objects.filter(assignment=self.assignment, student=self.student).exists())

    def test_double_extension_and_svg_blocking(self):
        from django.core.exceptions import ValidationError
        from Codex.validators import validate_secure_file_extension
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Double extension
        double_ext_file = SimpleUploadedFile("document.php.pdf", b"echo test", content_type="application/pdf")
        with self.assertRaises(ValidationError):
            validate_secure_file_extension(double_ext_file)

        # SVG file (XSS vector)
        svg_file = SimpleUploadedFile("image.svg", b"<svg><script>alert(1)</script></svg>", content_type="image/svg+xml")
        with self.assertRaises(ValidationError):
            validate_secure_file_extension(svg_file)

    def test_student_registration_with_licence(self):
        response = self.client.post(reverse('register'), {
            'username': 'new_l1_student',
            'email': 'l1@univ.fr',
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'user_type': 'student',
            'licence': 'L1',
            'password': 'SecurePassword123!',
            'password_confirmation': 'SecurePassword123!',
        })
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username='new_l1_student')
        self.assertEqual(created_user.licence, 'L1')
        self.assertEqual(created_user.user_type, 'student')

    def test_licence_access_restrictions(self):
        # Create an L1 student and an L2 student
        student_l1 = User.objects.create_user(username='stud_l1', password='password123', user_type='student', licence='L1')
        student_l2 = User.objects.create_user(username='stud_l2', password='password123', user_type='student', licence='L2')

        # Course strictly for L2
        course_l2 = Course.objects.create(
            title='Django Avance L2',
            code='INF202',
            licence='L2',
            teacher=self.teacher
        )
        res_l2 = CourseResource.objects.create(
            course=course_l2,
            title='Support L2'
        )

        # 1. Student L1 can VIEW the course detail page (consultation)
        self.client.force_login(student_l1)
        response = self.client.get(reverse('course_detail', args=[course_l2.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mode Consultation Seule')

        # 2. Student L1 CANNOT enroll in course L2
        response = self.client.get(reverse('enroll', args=[course_l2.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[course_l2.pk]))
        self.assertFalse(course_l2.students.filter(pk=student_l1.pk).exists())

        # 3. Student L1 CANNOT download L2 resources
        response = self.client.get(reverse('resource_download', args=[course_l2.pk, res_l2.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[course_l2.pk]))

        # 4. Student L2 CAN enroll in course L2
        self.client.force_login(student_l2)
        response = self.client.get(reverse('enroll', args=[course_l2.pk]))
        self.assertRedirects(response, reverse('course_detail', args=[course_l2.pk]))
        self.assertTrue(course_l2.students.filter(pk=student_l2.pk).exists())

        # 5. Teacher and Admin have full access
        self.assertTrue(course_l2.user_has_access(self.teacher))
        self.assertTrue(course_l2.user_has_access(self.admin))

    def test_teacher_creates_course_with_licence(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse('course_create'), {
            'title': 'Bases de Données L3',
            'code': 'BDD301',
            'category': 'Informatique',
            'licence': 'L3',
            'description': 'Cours destiné aux étudiants de Licence 3',
        })
        self.assertEqual(response.status_code, 302)
        course = Course.objects.get(code='BDD301')
        self.assertEqual(course.licence, 'L3')
        self.assertEqual(course.teacher, self.teacher)

    def test_announcement_licence_targeting_and_notifications(self):
        from Comptes.models import Notification
        # Ensure students for L1 and L2 exist
        s_l1 = User.objects.create_user(username='ann_student_l1', password='password123', user_type='student', licence='L1')
        s_l2 = User.objects.create_user(username='ann_student_l2', password='password123', user_type='student', licence='L2')

        # Admin creates announcement targeted specifically to L1
        self.client.force_login(self.admin)
        response = self.client.post(reverse('announcement_create'), {
            'title': 'Rentrée Licence 1',
            'content': 'Réunion de rentrée amphi A pour les L1 uniquement.',
            'licence': 'L1',
        })
        self.assertEqual(response.status_code, 302)
        ann_l1 = Announcement.objects.get(title='Rentrée Licence 1')
        self.assertEqual(ann_l1.licence, 'L1')

        # Verify notifications: student L1 got notification, student L2 did NOT
        self.assertTrue(Notification.objects.filter(recipient=s_l1, title__icontains='Rentrée Licence 1').exists())
        self.assertFalse(Notification.objects.filter(recipient=s_l2, title__icontains='Rentrée Licence 1').exists())

        # Verify listing: student L1 sees ann_l1, student L2 does NOT see ann_l1 in their default list
        self.client.force_login(s_l1)
        resp_l1 = self.client.get(reverse('announcement_list'))
        self.assertContains(resp_l1, 'Rentrée Licence 1')

        self.client.force_login(s_l2)
        resp_l2 = self.client.get(reverse('announcement_list'))
        self.assertNotContains(resp_l2, 'Rentrée Licence 1')

        # Admin and Teacher see all announcements
        self.client.force_login(self.teacher)
        resp_t = self.client.get(reverse('announcement_list'))
        self.assertContains(resp_t, 'Rentrée Licence 1')





