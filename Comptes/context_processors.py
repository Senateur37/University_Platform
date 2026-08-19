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
    unread_notifs = user_notifs.filter(is_read=False)

    return {
        'notifications_unread_count': unread_notifs.count(),
        'recent_notifications': user_notifs[:10],
        'unread_announcements_count': unread_notifs.filter(notification_type='announcement').count(),
        'unread_assignments_count': unread_notifs.filter(notification_type='assignment').count(),
        'unread_forum_count': unread_notifs.filter(notification_type='forum').count(),
    }
