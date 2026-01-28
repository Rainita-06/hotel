from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from hotel_app import views
from hotel_app.views import GymMemberViewSet, GymVisitViewSet, VoucherViewSet, BuildingViewSet, FloorViewSet, LocationTypeViewSet  # custom logout view
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from hotel_app.views import LocationFamilyViewSet, LocationViewSet
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
import os

router = DefaultRouter()
router.register(r'location-families', LocationFamilyViewSet, basename='locationfamily')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r"locations", LocationViewSet, basename="locations")
router.register(r'buildings', BuildingViewSet,basename="buildings")
router.register(r'floors',FloorViewSet,basename="floors")

router.register(r'types',LocationTypeViewSet,basename="types")
router.register(r'vouchers', VoucherViewSet, basename='voucher')

router.register(r'members', GymMemberViewSet, basename='gymmember')
router.register(r'visits', GymVisitViewSet, basename='gymvisit')
from django.contrib.auth import logout
from django.shortcuts import redirect

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    # Add cache control headers to prevent back button access
    response = redirect('/login/')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# Service worker views - must be served from root for proper scope
@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def firebase_messaging_sw(request):
    """Serve Firebase messaging service worker from root."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'firebase-messaging-sw.js')
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('// Service worker not found', content_type='application/javascript', status=404)

@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    """Serve main service worker from root."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('// Service worker not found', content_type='application/javascript', status=404)

def manifest_json(request):
    """Serve PWA manifest from root."""
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/manifest+json')
    except FileNotFoundError:
        return HttpResponse('{}', content_type='application/manifest+json', status=404)

urlpatterns = [
    # PWA Service Workers and Manifest (must be at root)
    path('firebase-messaging-sw.js', firebase_messaging_sw, name='firebase-messaging-sw'),
    path('sw.js', service_worker, name='service-worker'),
    path('manifest.json', manifest_json, name='manifest-json'),
    
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),
    
    path('api/', include('hotel_app.api_urls')),  # Updated API URL
    path('api/notification/', include('hotel_app.api_notification_urls')),  # Notification API URL
    

    # Screens
    # path('master-user/', views.MasterUserView.as_view(), name='master_user'),
    # path('master-location/', views.MasterLocationView.as_view(), name='master_location'),
    # path('hotel-dashboard/', views.HotelDashboardView.as_view(), name='hotel_dashboard'),
    # # path('breakfast-vouchers/', views.BreakfastVoucherView.as_view(), name='breakfast_vouchers'),
    # path('api/bulk-delete-users/', views.bulk_delete_users, name='bulk_delete_users'),
    # path('export-users/', views.export_users_csv, name='export_users'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    # Dashboard
    path('dashboard/', include('hotel_app.dashboard_urls', namespace='dashboard')),
    path('dashboard/locations/', views.locations_list, name='locations_list'),
    path('locations/add/', views.location_form, name='location_add'),
    
    path('location/', views.location_manage_view, name='location_manage'),
    path('locations/add/', views.add_family, name='add_family'),
    # path('locations/search/', views.search_families, name='search_families'),
    path('locations/search/', views.search_locations, name='search_locations'),
    # Public feedback form
    path('', include('hotel_app.urls')),
    
    # Twilio demo
    path('twilio/', include('hotel_app.twilio_urls')),

    path('locations/edit/<int:location_id>/', views.location_form, name='location_edit'),
    path('locations/delete/<int:location_id>/', views.location_delete, name='location_delete'),
    # path('request-types/', views.request_types_list, name='request_types_list'),
    path('family/delete/<int:family_id>/', views.family_delete, name='family_delete'),
    path('type/delete/<int:type_id>/', views.type_delete, name='type_delete'),
    path('floor/delete/<int:floor_id>/', views.floor_delete, name='floor_delete'),
    path('building/delete/<int:building_id>/', views.building_delete, name='building_delete'),
    # path("checklists/", views.checklist_list, name="checklist_list"),
    path("families/", views.location_manage_view, name="location_manage_view"),
    path("families/add/", views.family_form, name="family_add"),
    path("families/edit/<int:family_id>/", views.family_form, name="family_edit"),
    path("families/delete/<int:family_id>/", views.family_delete, name="family_delete"),
    path('buildings/<int:building_id>/upload-image/', views.upload_building_image, name='upload_building_image'),
    # Types
    path("types/", views.types_list, name="types_list"),
    path("types/add/", views.type_form, name="type_add"),
    path("types/edit/<int:type_id>/", views.type_form, name="type_edit"),
    path("types/delete/<int:type_id>/", views.type_delete, name="type_delete"),

    # Floors
    path("floors/", views.floors_list, name="floors_list"),
    path("floors/add/", views.floor_form, name="floor_form"),
    path("floors/<int:floor_id>/edit/", views.floor_form, name="floor_edit"),
    path("floors/<int:floor_id>/delete/", views.floor_delete, name="floor_delete"),

    # urls.py
    path('buildings/cards/', views.building_cards, name='building_cards'),
    path('buildings/<int:pk>/edit/', views.building_edit, name='building_edit'),

    # Buildings
    path("buildings/add/", views.building_form, name="building_add"),
    path("buildings/edit/<int:building_id>/", views.building_form, name="building_edit"),
    path("buildings/delete/<int:building_id>/", views.building_delete, name="building_delete"),
    path("bulk_import_locations/",views.bulk_import_locations,name="bulk_import_locations"),
    path("export_locations_csv/",views.export_locations_csv,name="export_locations_csv"),

    path("ajax/get-types/", views.get_types_by_family, name="get_types_by_family"),
path("clear-experience-message/", views.clear_experience_message, name="clear_experience_message"),

    
    path("bulk_import_buildings/",views.bulk_import_buildings,name="bulk_import_buildings"),
    path("bulk_import_floors/",views.bulk_import_floors,name="bulk_import_floors"),
    path("bulk_import_families/",views.bulk_import_families,name="bulk_import_families"),
      path("bulk_import_types/",views.bulk_import_types,name="bulk_import_types"),
      path("types/<int:type_id>/upload-image/", views.upload_type_image, name="upload_type_image"),
          path("family/<int:family_id>/upload-image/", views.upload_family_image, name="upload_family_image"),
path("ajax/get-floors/", views.get_floors_by_building, name="get_floors"),
    #Breakfast voucher
    path("checkin/", views.create_voucher_checkin, name="checkin_form"),
    path("voucher/<str:voucher_code>/", views.voucher_landing, name="voucher_landing"),
    path("checkout/<int:voucher_id>/",views.mark_checkout, name="checkout"),
    # path('voucher-checkout/<int:voucher_id>/', views.mark_checkout, name='mark_checkout'),

    path("scan/", views.scan_voucher_page, name="scan_voucher"),
    path("scan/<str:code>/", views.scan_voucher_page, name="scan_voucher"),
    path("api/vouchers/validate/", views.validate_voucher, name="validate_voucher"),
    path("report/vouchers/", views.breakfast_voucher_report, name="breakfast_voucher_report"),
    path("api/members/validate/", views.validate_member_qr, name="validate_member_qr"),
    
    #Gym
    path("members/add/", views.add_member, name="add_member"),
    path("members/", views.member_list, name="member_list"),
    path('members/<int:member_id>/', views.view_member, name='view_member'),
    path("members/<int:member_id>/edit/", views.edit_member, name="edit_member"),
    path("members/<int:member_id>/delete/", views.delete_member, name="delete_member"),
    path("members/scan/", views.validate_member_qr, name="validate_member_qr"),
    path("scan/gym/", views.scan_gym_page, name="scan_gym_page"),
    path("gym/report/", views.gym_report, name="gym_report"),
    path("data-checker/", views.data_checker, name="data_checker"),
     path('members/<int:member_id>/', views.member_detail, name='member_detail'),

     # urls.py

    # path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
    # path("tickets/review/", views.review_tickets, name="review_tickets"),
    # path("tickets/review/submit/<int:ticket_id>/", views.submit_ticket_review, name="submit_ticket_review"),
    # path("dashboard/", views.dashboard_view, name="dashboard_view"),
    path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
    path("dashboard/tickets/", views.tickets_view, name="tickets_view"),
    path('tickets/review/submit/<int:review_id>/', views.submit_ticket_review, name='submit_ticket_review'),
    
    # path("tickets/review/<int:ticket_id>/", views.submit_ticket_review, name="submit_ticket_review"),
    # path("dashboard/", views.dashboard_view, name="dashboard_view"),
        # path('tickets/review/', views.review_unclassified_tickets, name='review_unclassified_tickets'),
    # path('tickets/review/submit/<int:ticket_id>/', views.submit_ticket_review, name='submit_ticket_review'),
#  path("dashboard/tickets/", views.ticket_review_dashboard, name="ticket_review_dashboard"),

    #   path("dashboard/review-queue/", views.review_queue_view, name="review_queue_view"),
    # path("dashboard/review/<int:review_id>/submit/", views.submit_review, name="submit_review"),
    
    path('api/', include(router.urls)),
    
    #Api for authorization
    path("api/token-auth/", obtain_auth_token, name="api_token_auth"),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)