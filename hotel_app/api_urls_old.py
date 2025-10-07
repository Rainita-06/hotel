from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import (
    UserViewSet, DepartmentViewSet, UserGroupViewSet,
    LocationViewSet, ComplaintViewSet, BreakfastVoucherViewSet, ReviewViewSet,
    DashboardViewSet, CustomAuthToken, GuestViewSet,
    # New voucher system
    VoucherViewSet, VoucherScanViewSet, VoucherValidationView,
    validate_voucher_simple
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'user-groups', UserGroupViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'complaints', ComplaintViewSet)
router.register(r'breakfast-vouchers', BreakfastVoucherViewSet)  # Legacy
router.register(r'vouchers', VoucherViewSet)  # New voucher system
router.register(r'voucher-scans', VoucherScanViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'guests', GuestViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomAuthToken.as_view()),
    
    # Enhanced voucher validation endpoints
    path('vouchers/validate/', VoucherValidationView.as_view(), name='voucher_validate'),
    path('vouchers/validate/simple/', validate_voucher_simple, name='simple_voucher_validate'),

    # Legacy voucher management (keep for backward compatibility)
    path("issue-voucher/<int:guest_id>/", views.issue_voucher, name="issue_voucher"),
    path("issue-voucher/", views.issue_voucher_list, name="issue_voucher_list"),
    path("scan-voucher/", views.scan_voucher, name="scan_voucher_api"),
    path("scan-voucher-page/", views.scan_voucher_page, name="scan_voucher_page"),
    path("voucher-report/", views.voucher_report, name="voucher_report"),
]
