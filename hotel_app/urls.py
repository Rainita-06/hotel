from django.urls import path
from . import views

app_name = 'hotel_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('feedback/', views.feedback_form, name='feedback_form'),
    path('feedback/submit/', views.submit_feedback, name='submit_feedback'),
]