import os
import sys
import django
from django.utils import timezone
from datetime import timedelta

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Codex.settings")
django.setup()

from Comptes.models import User
from Cours.models import Course, CourseResource
from Missions.models import Assignment, Submission
from Annonces.models import Announcement

def seed():
    print("[+] Initialisation des donnees de demonstration pour Codex...")

    # 1. Nettoyage optionnel ou création d'utilisateurs
    admin, _ = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@university.edu",
            "first_name": "Administrateur",
            "last_name": "Campus",
            "user_type": "admin",
            "is_staff": True,
            "is_superuser": True,
            "is_validated": True,
            "filiere": "Direction des Systèmes d'Information",
        }
    )
    admin.set_password("admin123")
    admin.save()

    teacher1, _ = User.objects.get_or_create(
        username="prof_martin",
        defaults={
            "email": "jean.martin@university.edu",
            "first_name": "Jean",
            "last_name": "Martin",
            "user_type": "teacher",
            "is_validated": True,
            "filiere": "Informatique",
            "bio": "Enseignant-chercheur passionné d'Algorithmique et de Développement Web.",
        }
    )
    teacher1.set_password("prof1234")
    teacher1.save()

    teacher2, _ = User.objects.get_or_create(
        username="prof_dubois",
        defaults={
            "email": "marie.dubois@university.edu",
            "first_name": "Marie",
            "last_name": "Dubois",
            "user_type": "teacher",
            "is_validated": True,
            "filiere": "Mathématiques",
            "bio": "Professeur de Mathématiques Appliquées et Data Science.",
        }
    )
    teacher2.set_password("prof1234")
    teacher2.save()

    student1, _ = User.objects.get_or_create(
        username="alice",
        defaults={
            "email": "alice@etudiant.univ.fr",
            "first_name": "Alice",
            "last_name": "Lefebvre",
            "user_type": "student",
            "licence": "L2",
            "is_validated": True,
            "filiere": "Informatique L2",
        }
    )
    student1.licence = "L2"
    student1.set_password("etudiant123")
    student1.save()

    student2, _ = User.objects.get_or_create(
        username="bob",
        defaults={
            "email": "bob@etudiant.univ.fr",
            "first_name": "Bob",
            "last_name": "Rousseau",
            "user_type": "student",
            "licence": "L1",
            "is_validated": True,
            "filiere": "Informatique L1",
        }
    )
    student2.licence = "L1"
    student2.set_password("etudiant123")
    student2.save()

    print("[OK] Utilisateurs crees (admin: admin/admin123, enseignants: prof_martin/prof1234, etudiants: alice/etudiant123).")

    # 2. Création des cours
    c1, _ = Course.objects.get_or_create(
        code="INFO101",
        defaults={
            "title": "Introduction a l'Algorithmique et Python",
            "category": "Informatique",
            "licence": "L1",
            "description": "Apprenez les bases de la programmation en Python, la pensee algorithmique et la structure des donnees.",
            "teacher": teacher1,
        }
    )
    c1.licence = "L1"
    c1.save()

    c2, _ = Course.objects.get_or_create(
        code="INFO202",
        defaults={
            "title": "Developpement Web Avance avec Django",
            "category": "Informatique",
            "licence": "L2",
            "description": "Conception d'applications web robustes avec le framework Django, architecture MVT, bases de donnees et formulaires.",
            "teacher": teacher1,
        }
    )
    c2.licence = "L2"
    c2.save()

    c3, _ = Course.objects.get_or_create(
        code="MATH101",
        defaults={
            "title": "Algebre Lineaire et Analyse",
            "category": "Mathematiques",
            "licence": "L1",
            "description": "Matrices, espaces vectoriels, derivees et integrales appliquees a l'informatique et aux sciences.",
            "teacher": teacher2,
        }
    )
    c3.licence = "L1"
    c3.save()

    c4, _ = Course.objects.get_or_create(
        code="INFO303",
        defaults={
            "title": "Architecture Logicielle et Microservices",
            "category": "Informatique",
            "licence": "L3",
            "description": "Patrons de conception avances, architectures distribuees, conteneurisation Docker et APIs REST/GraphQL.",
            "teacher": teacher1,
        }
    )
    c4.licence = "L3"
    c4.save()

    # Inscription des étudiants
    c1.students.add(student1, student2)
    c2.students.add(student1)
    c3.students.add(student2)

    print("[OK] Cours et inscriptions mep.")

    # 3. Création de ressources pour les cours
    from django.core.files.base import ContentFile
    sample_pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 55>>stream\n"
        b"BT /F1 12 Tf 50 750 Td (Support de cours universitaire Codex) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000111 00000 n \n0000000212 00000 n \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n317\n%%EOF\n"
    )

    res1, _ = CourseResource.objects.get_or_create(
        course=c1,
        title="Support de cours 01 - Les Boucles et Fonctions",
        defaults={
            "description": "Diapositives du cours magistral n°1.",
        }
    )
    if not res1.file or not res1.file_base64:
        res1.file.save("Support_Python_L1.pdf", ContentFile(sample_pdf_bytes), save=True)

    res2, _ = CourseResource.objects.get_or_create(
        course=c2,
        title="Guide d'installation et Architecture Django",
        defaults={
            "description": "Fiche pratique pour initialiser un projet Django moderne.",
        }
    )
    if not res2.file or not res2.file_base64:
        res2.file.save("Guide_Django_L2.pdf", ContentFile(sample_pdf_bytes), save=True)

    # 4. Création de missions (devoirs)
    m1, _ = Assignment.objects.get_or_create(
        title="TP 1 : Algorithmes de Tri en Python",
        course=c1,
        defaults={
            "licence": "L1",
            "description": "Implementez le tri a bulles et le tri fusion en Python, puis comparez leur complexite temporelle sur 10 000 elements.",
            "max_points": 20.00,
            "due_date": timezone.now() + timedelta(days=7),
        }
    )
    m1.licence = "L1"
    if not m1.attachment or not m1.attachment_base64:
        m1.attachment.save("Sujet_TP1_Algorithmes.pdf", ContentFile(sample_pdf_bytes), save=False)
    m1.save()

    m2, _ = Assignment.objects.get_or_create(
        title="Projet : Creation de la plateforme d'evaluation",
        course=c2,
        defaults={
            "licence": "L2",
            "description": "Realisez une application Django complete avec modeles, vues, formulaires et templates personnalises.",
            "max_points": 20.00,
            "due_date": timezone.now() + timedelta(days=14),
        }
    )
    m2.licence = "L2"
    m2.save()

    # 5. Soumissions et notes
    sub1, _ = Submission.objects.get_or_create(
        assignment=m1,
        student=student1,
        defaults={
            "grade": 18.50,
            "feedback": "Excellente mise en oeuvre du tri fusion et analyse tres claire des performances !",
        }
    )

    Submission.objects.get_or_create(
        assignment=m1,
        student=student2,
        defaults={
            "feedback": "Copie recue, en cours de correction.",
        }
    )

    print("[OK] Missions et soumissions enregistrees.")

    # 6. Annonces
    Announcement.objects.get_or_create(
        title="Bienvenue sur la plateforme universitaire Codex !",
        defaults={
            "content": "Decouvrez votre nouvel espace de travail interactif. Consultez vos cours, soumettez vos devoirs et suivez vos evaluations en temps reel.",
            "author": admin,
            "is_global": True,
        }
    )

    Announcement.objects.get_or_create(
        title="Rappel : Rendez-vous pour le TP1 de Python",
        defaults={
            "content": "N'oubliez pas de consulter le support de cours avant la seance de vendredi.",
            "course": c1,
            "author": teacher1,
            "is_global": False,
        }
    )

    print("[OK] Annonces creees avec succes.")

    # 7. Forum Categories & Topics
    from Forum.models import ForumCategory, ForumTopic, ForumPost

    cat1, _ = ForumCategory.objects.get_or_create(name="Questions de Cours", slug="questions-de-cours", defaults={"description": "Entraide et explications sur les cours.", "icon": "📚"})
    cat2, _ = ForumCategory.objects.get_or_create(name="Projets & TP", slug="projets-et-tp", defaults={"description": "Discussions autour des projets et devoirs.", "icon": "💻"})
    cat3, _ = ForumCategory.objects.get_or_create(name="Général & Vie Étudiante", slug="general", defaults={"description": "Discussions libres, événements et vie de campus.", "icon": "💬"})

    topic1, _ = ForumTopic.objects.get_or_create(
        title="Comment bien aborder la récursivité en Python ?",
        defaults={
            "licence": "L1",
            "category": cat1,
            "course": c1,
            "author": student2,
            "content": "Bonjour à tous, j'ai un peu de mal avec les cas de base dans les fonctions récursives. Auriez-vous des exemples simples ou des conseils pour mieux visualiser le principe ?",
            "is_pinned": True,
        }
    )
    topic1.licence = "L1"
    topic1.save()

    ForumPost.objects.get_or_create(
        topic=topic1,
        author=teacher1,
        defaults={
            "content": "Bonjour ! Pense toujours à la récursivité comme une poupée russe. Le cas de base est la plus petite poupée qui s'ouvre d'elle-même sans nouvel appel. Nous reverrons cela ensemble lors du prochain TP !",
        }
    )

    topic2, _ = ForumTopic.objects.get_or_create(
        title="Conseils pour l'architecture Django et les modèles L2",
        defaults={
            "licence": "L2",
            "category": cat2,
            "course": c2,
            "author": student1,
            "content": "Bonjour la promo L2, comment organisez-vous les ForeignKey et relations ManyToMany dans vos applications ?",
            "is_pinned": False,
        }
    )
    topic2.licence = "L2"
    topic2.save()

    print("[OK] Forum initialisé avec des catégories et discussions par Licence.")

    # 8. Notifications de test
    from Comptes.models import Notification
    from django.urls import reverse

    for user in [admin, teacher1, teacher2, student1, student2]:
        if not Notification.objects.filter(recipient=user).exists():
            Notification.objects.create(
                recipient=user,
                notification_type='announcement',
                title="📢 Bienvenue sur Codex EUTG !",
                message="Bienvenue dans votre nouvel espace campus interactif.",
                link=reverse('dashboard')
            )
            Notification.objects.create(
                recipient=user,
                notification_type='assignment',
                title="🎯 Nouveau devoir TP1 Python",
                message="Consultez les détails et la date limite dans l'onglet Missions.",
                link=reverse('assignment_list')
            )
            Notification.objects.create(
                recipient=user,
                notification_type='forum',
                title="💬 Discussion récursivité en Python",
                message="Une réponse a été publiée sur le forum.",
                link=reverse('topic_list')
            )

    print("[OK] Notifications de démonstration générées.")
    print("[DONE] Donnees de test pretes !")

if __name__ == "__main__":
    seed()
