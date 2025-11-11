from django.conf import settings
from hotel_app.section_permissions import user_has_section_permission
from hotel_app.models import Section

def nav_permissions(request):
    user = request.user
    is_admin = (
        user.is_authenticated
        and (user.is_superuser or user.groups.filter(name=getattr(settings, "ADMINS_GROUP", "Admins")).exists())
    )
    
    # Get user role
    user_role = None
    if user.is_authenticated and hasattr(user, 'userprofile'):
        user_role = user.userprofile.role
        if not user_role:
            primary_group = user.groups.first()
            if primary_group:
                user_role = primary_group.name
    
    # Get section permissions for the user
    section_permissions = {}
    if user.is_authenticated:
        try:
            # Get all active sections (handle case where table doesn't exist yet)
            sections = Section.objects.filter(is_active=True)
            for section in sections:
                can_view = user_has_section_permission(user, section.name, 'view')
                can_add = user_has_section_permission(user, section.name, 'add')
                can_change = user_has_section_permission(user, section.name, 'change')
                can_delete = user_has_section_permission(user, section.name, 'delete')
                section_permissions[section.name] = {
                    'view': can_view,
                    'add': can_add,
                    'change': can_change,
                    'delete': can_delete,
                    'edit': can_add or can_change or can_delete,
                }
        except Exception:
            # If Section table doesn't exist or other error, return empty dict
            # This allows the app to work even if migrations haven't been run yet
            section_permissions = {}
    
    return {
        "is_admin": is_admin,
        "ADMINS_GROUP": getattr(settings, "ADMINS_GROUP", "Admins"),
        "USERS_GROUP": getattr(settings, "USERS_GROUP", "Users"),
        "user_role": user_role,
        "section_permissions": section_permissions,
    }