from django.urls import include, path

from . import api_views, api_whatsapp_views

urlpatterns = [
    path('users/me/', api_views.current_user, name='api-current-user'),
    path('whatsapp/webhook', api_whatsapp_views.whatsapp_webhook, name='api-whatsapp-webhook-no-slash'),
    path('whatsapp/webhook/', api_whatsapp_views.whatsapp_webhook, name='api-whatsapp-webhook'),
    path('', include('hotel_app.api_notification_urls')),
]