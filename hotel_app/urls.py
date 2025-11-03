from django.urls import path
from . import views

app_name = 'hotel_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('feedback/', views.feedback_form, name='feedback_form'),
    path('feedback/submit/', views.submit_feedback, name='submit_feedback'),
    path('twilio/send-whatsapp/', views.send_whatsapp_notification, name='send_whatsapp_notification'),
    path('twilio/send-templated-whatsapp/', views.send_templated_whatsapp, name='send_templated_whatsapp'),
]