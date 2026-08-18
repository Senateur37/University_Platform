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
        fields = ('title', 'category', 'course', 'content')
        labels = {
            'title': 'Titre de la discussion',
            'category': 'Catégorie du forum',
            'course': 'Cours associé (Optionnel)',
            'content': 'Message principal / Question',
        }


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
    query = request.GET.get('q', '').strip()

    topics = ForumTopic.objects.select_related('author', 'category', 'course').prefetch_related('posts').all()

    if category_slug:
        topics = topics.filter(category__slug=category_slug)

    if query:
        topics = topics.filter(Q(title__icontains=query) | Q(content__icontains=query))

    categories = ForumCategory.objects.all()

    return render(request, 'forum/list.html', {
        'topics': topics,
        'categories': categories,
        'selected_category': category_slug,
        'query': query,
    })


def topic_detail(request, pk):
    topic = get_object_or_404(ForumTopic.objects.select_related('author', 'category', 'course'), pk=pk)

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
    form = TopicForm(request.POST or None)
    if form.is_valid():
        topic = form.save(commit=False)
        topic.author = request.user
        topic.save()
        messages.success(request, "Sujet de discussion créé avec succès.")
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

    form = TopicForm(request.POST or None, instance=topic)
    if form.is_valid():
        form.save()
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
    if topic.is_closed and not request.user.is_teacher_or_admin:
        messages.error(request, "Cette discussion est verrouillée.")
        return redirect('topic_detail', topic.pk)

    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.topic = topic
        post.author = request.user
        post.save()
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
