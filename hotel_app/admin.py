from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from . import models

User = get_user_model()


# helper to determine 'admin' users (superuser OR in Admin group)
def _is_admin_user(user):
    if not user or not user.is_active:
        return False
    if user.is_superuser:
        return True
    try:
        return user.groups.filter(name='Admin').exists()
    except Exception:
        return False


# Register MasterUser proxy (admin only)
class MasterUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')

    def has_module_permission(self, request):
        return _is_admin_user(request.user)

    def get_model_perms(self, request):
        # hide the model from non-admin users in the admin index
        return super().get_model_perms(request) if _is_admin_user(request.user) else {}


# Register MasterLocation proxy (admin only)
class MasterLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'floor', 'capacity')
    search_fields = ('name', 'room_no')

    def has_module_permission(self, request):
        return _is_admin_user(request.user)

    def get_model_perms(self, request):
        return super().get_model_perms(request) if _is_admin_user(request.user) else {}


# Hotel Dashboard Services: superficial model using ServiceRequest as placeholder
class HotelDashboardServiceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at') if hasattr(models.ServiceRequest, 'created_at') else ('__str__',)

    def has_module_permission(self, request):
        # visible to staff and superusers
        return request.user.is_active and request.user.is_staff


# # Voucher admin (visible to staff)
# @admin.register(models.Voucher)
# class VoucherAdmin(admin.ModelAdmin):
#     list_display = ('voucher_code', 'guest_name', 'room_number', 'expiry_date', 'redeemed')
#     search_fields = ('guest_name', 'voucher_code', 'room_number')
#     list_filter = ('redeemed', 'expiry_date')
#     readonly_fields = ('voucher_code', 'created_at', 'updated_at')
#     ordering = ('-created_at',)

#     def has_module_permission(self, request):
#         return request.user.is_active and request.user.is_staff


# Voucher Scan admin for tracking redemptions
# @admin.register(models.VoucherScan)
# class VoucherScanAdmin(admin.ModelAdmin):
#     list_display = ('voucher', 'scanned_at', 'scanned_by_user')
#     search_fields = ('voucher__voucher_code', 'voucher__guest_name')
#     readonly_fields = ('scanned_at',)
#     ordering = ('-scanned_at',)
    
#     def has_module_permission(self, request):
#         return request.user.is_active and request.user.is_staff


# Bulk register models (exclude Location & UserProfile since they have custom admins)
models_to_register = [
    models.Department, models.UserGroup, models.UserGroupMembership,
    models.Building, models.Floor, models.LocationFamily, models.LocationType,
    models.RequestFamily, models.WorkFamily, models.Workflow, models.WorkflowStep, models.WorkflowTransition,
    models.Checklist, models.ChecklistItem, models.RequestType, models.RequestKeyword,
    models.ServiceRequest, models.ServiceRequestStep, models.ServiceRequestChecklist,
    models.WhatsAppConversation, models.WhatsAppMessage, models.UnmatchedRequest,
    models.FeedbackQuestion, models.FeedbackSession, models.FeedbackResponse,
    models.Guest, models.GuestComment,
    models.GymMember, models.GymVisitor, models.GymVisit,
]

for model in models_to_register:
    if model not in admin.site._registry:  # avoids AlreadyRegistered
        admin.site.register(model)


# Ensure Department admin allows editing/assigning users (via UserProfile) inline
class DepartmentUserProfileInline(admin.TabularInline):
    model = models.UserProfile
    fk_name = 'department'
    fields = ('user', 'full_name', 'title', 'phone', 'enabled')
    extra = 0
    show_change_link = True


# Unregister existing Department registration if present, then register custom admin
if models.Department in admin.site._registry:
    try:
        admin.site.unregister(models.Department)
    except Exception:
        pass


@admin.register(models.Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    inlines = [DepartmentUserProfileInline]


# Add UserProfile inline to the User admin so department can be set when editing a user
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin


class UserProfileStackedInline(admin.StackedInline):
    model = models.UserProfile
    can_delete = False
    verbose_name_plural = 'profile'
    fk_name = 'user'


try:
    # If User is already registered, unregister and re-register with inline
    if User in admin.site._registry:
        admin.site.unregister(User)
except Exception:
    pass


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    inlines = (UserProfileStackedInline,)


# Custom Admin Classes
@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'type', 'building', 'floor', 'capacity')
    search_fields = ('name', 'room_no')
    list_filter = ('building', 'floor', 'type', 'family')


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'department', 'title', 'phone', 'role')
    search_fields = ('full_name', 'user__username', 'phone')
    list_filter = ('department', 'title', 'role')
    fields = ('user', 'full_name', 'department', 'title', 'phone', 'role', 'enabled', 'avatar_url', 'timezone')


@admin.register(models.Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_active', 'created_at')
    search_fields = ('name', 'display_name', 'description')
    list_filter = ('is_active', 'created_at')
    fields = ('name', 'display_name', 'description', 'is_active')


# Register proxies and models if not already registered
# MasterUser proxy registration
try:
    admin.site.register(models.MasterUser, MasterUserAdmin)
except Exception:
    # already registered or other issue
    pass

# MasterLocation proxy registration
try:
    admin.site.register(models.MasterLocation, MasterLocationAdmin)
except Exception:
    pass

# Hotel Dashboard Services: surface ServiceRequest as 'Hotel Dashboard Services' via a proxy admin entry
# We won't create a new model; we rely on ServiceRequest being registered already. If not, register a minimal wrapper.
if models.ServiceRequest not in admin.site._registry:
    try:
        admin.site.register(models.ServiceRequest, HotelDashboardServiceAdmin)
    except Exception:
        pass
