"""
Middleware to check user permissions after login and redirect users without proper roles.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser


class UserPermissionCheckMiddleware:
    """
    Middleware to check if authenticated users have proper roles/permissions.
    If a user has no role assigned and no permissions, they are redirected to a no-access page.
    """
    
    # Pages that don't require permission checks
    EXEMPT_PATHS = [
        '/login/',
        '/logout/',
        '/password-reset/',
        '/admin/',
        '/static/',
        '/media/',
        '/api/',
        '/dashboard/no-access/',
        '/dashboard/permission-denied/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user needs permission verification
        if self.should_check_permissions(request):
            if not self.user_has_access(request.user):
                # Redirect to no-access page
                return redirect('dashboard:no_access')
        
        response = self.get_response(request)
        return response
    
    def should_check_permissions(self, request):
        """Determine if we should check permissions for this request."""
        # Don't check for anonymous users
        if isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
            return False
        
        # Don't check for exempt paths
        path = request.path
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return False
        
        return True
    
    def user_has_access(self, user):
        """
        Check if user has any access rights.
        Returns True if user has at least one of:
        - Is superuser
        - Has a role assigned in UserProfile
        - Belongs to at least one group
        - Has at least one permission
        """
        # Superusers always have access
        if user.is_superuser:
            return True
        
        # Check if user has a role assigned
        try:
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                # Check if role is assigned and not empty
                if profile.role and profile.role.strip():
                    return True
        except Exception:
            pass
        
        # Check if user belongs to any group
        try:
            if user.groups.exists():
                return True
        except Exception:
            pass
        
        # Check if user has any permissions directly assigned
        try:
            if user.user_permissions.exists():
                return True
        except Exception:
            pass
        
        # Check if user has access to any section
        try:
            from hotel_app.section_permissions import user_has_section_permission
            from hotel_app.models import Section
            
            # Check if user has view permission for any active section
            sections = Section.objects.filter(is_active=True)
            for section in sections:
                if user_has_section_permission(user, section.name, 'view'):
                    return True
        except Exception:
            pass
        
        # If no access found, user doesn't have access
        return False
