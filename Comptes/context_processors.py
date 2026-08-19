from .models import Notification

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

    # Ensure existing users always have welcome notifications if empty
    if not user_notifs.exists():
        welcome_items = [
            {
                'type': 'announcement',
                'title': '📢 Bienvenue sur la plateforme EUTG !',
                'message': 'Consultez vos cours, devoirs et annonces depuis votre espace central.',
                'link': '/dashboard/'
            },
            {
                'type': 'assignment',
                'title': '🎯 Vos devoirs et travaux à rendre',
                'message': 'Découvrez vos missions et téléversez vos travaux dans l\'onglet Missions.',
                'link': '/missions/'
            },
            {
                'type': 'forum',
                'title': '💬 Forum de discussion interactif',
                'message': 'Posez vos questions et échangez avec vos enseignants et camarades.',
                'link': '/forum/'
            }
        ]
        for item in welcome_items:
            Notification.objects.get_or_create(
                recipient=request.user,
                notification_type=item['type'],
                title=item['title'],
                defaults={
                    'message': item['message'],
                    'link': item['link'],
                    'is_read': False
                }
            )
        user_notifs = Notification.objects.filter(recipient=request.user)

    unread_notifs = user_notifs.filter(is_read=False)

    return {
        'notifications_unread_count': unread_notifs.count(),
        'recent_notifications': user_notifs[:10],
        'unread_announcements_count': unread_notifs.filter(notification_type='announcement').count(),
        'unread_assignments_count': unread_notifs.filter(notification_type='assignment').count(),
        'unread_forum_count': unread_notifs.filter(notification_type='forum').count(),
    }
