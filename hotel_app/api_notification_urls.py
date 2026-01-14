from django.urls import path
from . import api_views

urlpatterns = [
    # Notification Management
    path('notifications/', api_views.get_notifications, name='get-notifications'),
    path('notifications/all/', api_views.get_all_notifications, name='get-all-notifications'),
    path('notifications/<int:notification_id>/read/', api_views.mark_notification_as_read, name='mark-notification-as-read'),
    path('notifications/read-all/', api_views.mark_all_notifications_as_read, name='mark-all-notifications-as-read'),
    path('notifications/<int:notification_id>/delete/', api_views.delete_notification, name='delete-notification'),
    
    # FCM Token Management
    path('save-fcm-token/', api_views.save_fcm_token, name='save-fcm-token'),
    path('delete-fcm-token/', api_views.delete_fcm_token, name='delete-fcm-token'),
]
