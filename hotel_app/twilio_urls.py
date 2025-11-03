from django.urls import path
from . import views

app_name = 'twilio'

urlpatterns = [
    path('', views.twilio_demo, name='twilio_demo'),
    path('send-whatsapp/', views.send_whatsapp_notification, name='send_whatsapp_notification'),
    path('send-templated-whatsapp/', views.send_templated_whatsapp, name='send_templated_whatsapp'),
]