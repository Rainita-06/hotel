from django.contrib import admin
from django.urls import path, include
from hotel_app import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from hotel_app.views import GymMemberViewSet, GymVisitViewSet, VoucherViewSet, BuildingViewSet, FloorViewSet, LocationTypeViewSet, logout_view, signup_view  # custom logout view
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from hotel_app.views import LocationFamilyViewSet, LocationViewSet

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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),

    
    path('api/', include('hotel_app.api_urls')),  # Updated API URL
    path('api/notification/', include('hotel_app.api_notification_urls')),  # Notification API URL
    

    # Screens
    path('master-user/', views.MasterUserView.as_view(), name='master_user'),
    path('master-location/', views.MasterLocationView.as_view(), name='master_location'),
    path('hotel-dashboard/', views.HotelDashboardView.as_view(), name='hotel_dashboard'),
    # path('breakfast-vouchers/', views.BreakfastVoucherView.as_view(), name='breakfast_vouchers'),
    path('api/bulk-delete-users/', views.bulk_delete_users, name='bulk_delete_users'),
    path('export-users/', views.export_users_csv, name='export_users'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path("signup/", signup_view, name="signup"),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    # Dashboard
    path('dashboard/', include('hotel_app.dashboard_urls', namespace='dashboard')),
    path('locations/', views.locations_list, name='locations_list'),
    path('locations/add/', views.location_form, name='location_add'),
    
    path('location/', views.location_manage_view, name='location_manage'),
    path('locations/add/', views.add_family, name='add_family'),
    # path('locations/search/', views.search_families, name='search_families'),
    path('locations/search/', views.search_locations, name='search_locations'),

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
    
    #Breakfast voucher
    path("checkin/", views.create_voucher_checkin, name="checkin_form"),
    path("voucher/<str:voucher_code>/", views.voucher_landing, name="voucher_landing"),
    path("checkout/<int:voucher_id>/",views.mark_checkout, name="checkout"),
    path("scan/", views.scan_voucher_page, name="scan_voucher"),
    path("scan/<str:code>/", views.scan_voucher, name="scan_voucher"),
    path("api/vouchers/validate/", views.validate_voucher, name="validate_voucher"),
    path("report/vouchers/", views.breakfast_voucher_report, name="breakfast_voucher_report"),
    path("api/members/validate/", views.validate_member_qr, name="validate_member_qr"),

    #Gym
    path("members/add/", views.add_member, name="add_member"),
    path("members/", views.member_list, name="member_list"),
    path("members/<int:member_id>/edit/", views.edit_member, name="edit_member"),
    path("members/<int:member_id>/delete/", views.delete_member, name="delete_member"),
    path("members/scan/", views.validate_member_qr, name="validate_member_qr"),
    path("scan/gym/", views.scan_gym_page, name="scan_gym_page"),
    path("gym/report/", views.gym_report, name="gym_report"),
    path("data-checker/", views.data_checker, name="data_checker"),
    

    path('api/', include(router.urls)),
    
    #Api for authorization
    path("api/token-auth/", obtain_auth_token, name="api_token_auth"),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)