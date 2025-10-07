from django.urls import path, include

urlpatterns = [
    # Include notification API URLs
    path('', include('hotel_app.api_notification_urls')),
]