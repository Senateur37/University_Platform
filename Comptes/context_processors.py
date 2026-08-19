from .models import Notification
from django.urls import reverse

def notifications_context(request):
    if not request.user.is_authenticated:
        return {
            'notifications_unread_count': 0,
            'recent_notifications': [],
            'unread_announcements_count': 0,
            'unread_assignments_count': 0,
            'unread_forum_count': 0,
        }

    user_notifs = Notification.objects.filter(recipient=request.user)

    # Auto-generate welcome notifications if user has 0 notifications
    if not user_notifs.exists():
        try:
            Notification.objects.bulk_create([
                Notification(
                    recipient=request.user,
                    notification_type='announcement',
                    title="📢 Bienvenue sur la plateforme EUTG !",
                    message="Consultez vos cours, devoirs et annonces depuis votre espace.",
                    link=reverse('dashboard')
                ),
                Notification(
                    recipient=request.user,
                    notification_type='assignment',
                    title="🎯 Vos devoirs et travaux à rendre",
                    message="Découvrez vos missions et déposez vos devoirs dans l'onglet Missions.",
                    link=reverse('assignment_list')
                ),
                Notification(
                    recipient=request.user,
                    notification_type='forum',
                    title="💬 Forum de discussion interactif",
                    message="Posez vos questions et échangez avec vos enseignants et camarades.",
                    link=reverse('topic_list')
                ),
            ])
            user_notifs = Notification.objects.filter(recipient=request.user)
        except Exception:
            pass

    unread_notifs = user_notifs.filter(is_read=False)

    return {
        'notifications_unread_count': unread_notifs.count(),
        'recent_notifications': user_notifs[:10],
        'unread_announcements_count': unread_notifs.filter(notification_type='announcement').count(),
        'unread_assignments_count': unread_notifs.filter(notification_type='assignment').count(),
        'unread_forum_count': unread_notifs.filter(notification_type='forum').count(),
    }
