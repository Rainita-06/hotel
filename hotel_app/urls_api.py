from django.urls import path
from . import api_views

urlpatterns = [
    # User Management
    path('users/', api_views.UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', api_views.UserDetail.as_view(), name='user-detail'),
    
    # Department Management
    path('departments/', api_views.DepartmentList.as_view(), name='department-list'),
    path('departments/<int:pk>/', api_views.DepartmentDetail.as_view(), name='department-detail'),
    
    # User Group Management
    path('groups/', api_views.UserGroupList.as_view(), name='group-list'),
    path('groups/<int:pk>/', api_views.UserGroupDetail.as_view(), name='group-detail'),
    
    # Location Management
    path('locations/', api_views.LocationList.as_view(), name='location-list'),
    path('locations/<int:pk>/', api_views.LocationDetail.as_view(), name='location-detail'),
    
    # Service Request Management
    path('service-requests/', api_views.ServiceRequestList.as_view(), name='service-request-list'),
    path('service-requests/<int:pk>/', api_views.ServiceRequestDetail.as_view(), name='service-request-detail'),
    
    # Voucher Management
    path('vouchers/', api_views.VoucherList.as_view(), name='voucher-list'),
    path('vouchers/<int:pk>/', api_views.VoucherDetail.as_view(), name='voucher-detail'),
    
    # Guest Comment Management
    path('guest-comments/', api_views.GuestCommentList.as_view(), name='guest-comment-list'),
    path('guest-comments/<int:pk>/', api_views.GuestCommentDetail.as_view(), name='guest-comment-detail'),
    
    # Notification Management
    path('notifications/', api_views.get_notifications, name='get-notifications'),
    path('notifications/all/', api_views.get_all_notifications, name='get-all-notifications'),
    path('notifications/<int:notification_id>/read/', api_views.mark_notification_as_read, name='mark-notification-as-read'),
    path('notifications/read-all/', api_views.mark_all_notifications_as_read, name='mark-all-notifications-as-read'),
    path('notifications/<int:notification_id>/delete/', api_views.delete_notification, name='delete-notification'),
]