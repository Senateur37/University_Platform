from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q, F
from django import forms

from Comptes.decorateurs import user_type_required
from .models import ForumCategory, ForumTopic, ForumPost


class TopicForm(forms.ModelForm):
    class Meta:
        model = ForumTopic
        fields = ('title', 'licence', 'category', 'course', 'content')
        labels = {
            'title': 'Titre de la discussion',
            'licence': 'Espace / Forum de discussion',
            'category': 'Catégorie du forum',
            'course': 'Cours associé (Optionnel)',
            'content': 'Message principal / Question',
        }
        help_texts = {
            'licence': 'Sélectionnez le forum dédié à votre promotion (L1, L2, L3) ou le forum général.',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated and user.user_type == 'student':
            allowed_choices = [("ALL", "Forum Général (Tout le campus)")]
            if user.licence:
                licence_labels = dict(ForumTopic.LICENCE_CHOICES)
                allowed_choices.insert(0, (user.licence, licence_labels.get(user.licence, f"Forum Licence {user.licence}")))
                if not self.instance.pk and 'licence' not in self.initial:
                    self.initial['licence'] = user.licence
            self.fields['licence'].choices = allowed_choices


class PostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ('content',)
        labels = {
            'content': 'Votre réponse',
        }
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Écrivez votre réponse ici...'}),
        }


def topic_list(request):
    category_slug = request.GET.get('cat', '').strip()
    selected_licence = request.GET.get('licence', '').strip()
    query = request.GET.get('q', '').strip()
    user = request.user

    try:
        queryset = ForumTopic.objects.select_related('author', 'category', 'course').prefetch_related('posts').all()

        # Filtrage par droits de l'utilisateur : chaque Licence a son propre espace
        if user.is_authenticated:
            if user.user_type == 'student':
                student_filter = Q(licence='ALL') | Q(licence='') | Q(licence__isnull=True)
                if user.licence:
                    student_filter |= Q(licence=user.licence)
                queryset = queryset.filter(student_filter)
        else:
            queryset = queryset.filter(Q(licence='ALL') | Q(licence='') | Q(licence__isnull=True))

        # Filtrage par Licence demandé via l'URL
        if selected_licence:
            if selected_licence == 'ALL':
                queryset = queryset.filter(licence='ALL')
            elif user.is_teacher_or_admin or (user.is_authenticated and user.licence == selected_licence):
                queryset = queryset.filter(licence=selected_licence)

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(content__icontains=query))

        topics = list(queryset)
        categories = list(ForumCategory.objects.all())
    except Exception:
        topics = []
        categories = []

    return render(request, 'forum/list.html', {
        'topics': topics,
        'categories': categories,
        'selected_category': category_slug,
        'selected_licence': selected_licence,
        'licence_choices': ForumTopic.LICENCE_CHOICES,
        'query': query,
    })


def topic_detail(request, pk):
    topic = get_object_or_404(ForumTopic.objects.select_related('author', 'category', 'course'), pk=pk)

    # Vérification des droits d'accès selon la Licence
    if not topic.user_has_access(request.user):
        messages.error(
            request, 
            f"Accès refusé : cette discussion appartient au {topic.get_licence_display()} et est réservée aux étudiants concernés."
        )
        return redirect('topic_list')

    # Increment view count
    ForumTopic.objects.filter(pk=pk).update(views_count=F('views_count') + 1)
    topic.refresh_from_db()

    posts = topic.posts.select_related('author').all()
    form = PostForm()

    is_author_or_admin = request.user.is_authenticated and (
        request.user == topic.author or request.user.is_teacher_or_admin
    )

    return render(request, 'forum/detail.html', {
        'topic': topic,
        'posts': posts,
        'form': form,
        'is_author_or_admin': is_author_or_admin,
    })


@login_required
def topic_create(request):
    form = TopicForm(request.POST or None, user=request.user)
    if form.is_valid():
        topic = form.save(commit=False)
        topic.author = request.user
        if request.user.user_type == 'student' and topic.licence not in ['ALL', request.user.licence]:
            topic.licence = request.user.licence or 'ALL'
        topic.save()
        messages.success(request, f"Discussion publiée dans le {topic.get_licence_display()}.")
        return redirect('topic_detail', topic.pk)

    return render(request, 'form.html', {
        'form': form,
        'title': 'Lancer une nouvelle discussion',
        'submit_label': 'Publier le sujet',
    })


@login_required
def topic_edit(request, pk):
    topic = get_object_or_404(ForumTopic, pk=pk)
    if request.user != topic.author and not request.user.is_teacher_or_admin:
        messages.error(request, "Action non autorisée.")
        return redirect('topic_detail', topic.pk)

    form = TopicForm(request.POST or None, instance=topic, user=request.user)
    if form.is_valid():
        topic = form.save(commit=False)
        if request.user.user_type == 'student' and topic.licence not in ['ALL', request.user.licence]:
            topic.licence = request.user.licence or 'ALL'
        topic.save()
        messages.success(request, "Sujet mis à jour.")
        return redirect('topic_detail', topic.pk)

    return render(request, 'form.html', {
        'form': form,
        'title': f'Modifier : {topic.title}',
        'submit_label': 'Enregistrer',
    })


@login_required
def topic_delete(request, pk):
    topic = get_object_or_404(ForumTopic, pk=pk)
    if request.user != topic.author and not request.user.is_teacher_or_admin:
        messages.error(request, "Action non autorisée.")
        return redirect('topic_detail', topic.pk)

    if request.method == 'POST':
        title = topic.title
        topic.delete()
        messages.success(request, f"La discussion '{title}' a été supprimée.")
        return redirect('topic_list')

    return render(request, 'form.html', {
        'title': f'Confirmer la suppression de la discussion : {topic.title}',
        'submit_label': 'Oui, supprimer définitivement',
        'confirm_message': True,
    })


@login_required
def post_create(request, pk):
    topic = get_object_or_404(ForumTopic, pk=pk)
    if not topic.user_has_access(request.user):
        messages.error(request, f"Accès refusé : vous n'avez pas accès au {topic.get_licence_display()}.")
        return redirect('topic_list')

    if topic.is_closed and not request.user.is_teacher_or_admin:
        messages.error(request, "Cette discussion est verrouillée.")
        return redirect('topic_detail', topic.pk)

    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.topic = topic
        post.author = request.user
        post.save()

        # Notify topic author if not self
        if topic.author != request.user:
            from Comptes.models import Notification
            from django.urls import reverse
            Notification.objects.create(
                recipient=topic.author,
                notification_type='forum',
                title=f"💬 Nouvelle réponse : {topic.title}",
                message=f"{request.user.get_full_name() or request.user.username} a répondu à votre sujet.",
                link=reverse('topic_detail', args=[topic.pk])
            )

        messages.success(request, "Votre réponse a été publiée.")
    return redirect('topic_detail', topic.pk)


@login_required
def post_delete(request, pk, post_pk):
    topic = get_object_or_404(ForumTopic, pk=pk)
    post = get_object_or_404(ForumPost, pk=post_pk, topic=topic)
    if request.user != post.author and not request.user.is_teacher_or_admin:
        messages.error(request, "Action non autorisée.")
        return redirect('topic_detail', topic.pk)

    post.delete()
    messages.success(request, "Réponse supprimée.")
    return redirect('topic_detail', topic.pk)


@login_required
def topic_toggle_pin(request, pk):
    topic = get_object_or_404(ForumTopic, pk=pk)
    if not request.user.is_teacher_or_admin:
        messages.error(request, "Action réservée aux enseignants et administrateurs.")
        return redirect('topic_detail', topic.pk)

    topic.is_pinned = not topic.is_pinned
    topic.save()
    status = "épinglée" if topic.is_pinned else "désépinglée"
    messages.success(request, f"La discussion a été {status}.")
    return redirect('topic_detail', topic.pk)


@login_required
def topic_toggle_close(request, pk):
    topic = get_object_or_404(ForumTopic, pk=pk)
    if not request.user.is_teacher_or_admin:
        messages.error(request, "Action réservée aux enseignants et administrateurs.")
        return redirect('topic_detail', topic.pk)

    topic.is_closed = not topic.is_closed
    topic.save()
    status = "verrouillée" if topic.is_closed else "déverrouillée"
    messages.success(request, f"La discussion a été {status}.")
    return redirect('topic_detail', topic.pk)
