from django.urls import include, path

from . import api_views

urlpatterns = [
    path('users/me/', api_views.current_user, name='api-current-user'),
    path('', include('hotel_app.api_notification_urls')),
]