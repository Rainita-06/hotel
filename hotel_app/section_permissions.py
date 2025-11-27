"""
Section-based permission decorators and mixins for views.

This module provides decorators for function-based views and mixins for
class-based views to check section-based permissions.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import AccessMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from hotel_app.models import Section


def get_section_permission(section_name, action):
    """
    Get permission codename for a section and action.
    
    Args:
        section_name: Name of the section (e.g., 'users', 'locations')
        action: Permission action ('view', 'add', 'change', 'delete')
    
    Returns:
        Permission codename string (e.g., 'view_users')
    """
    try:
        section = Section.objects.get(name=section_name, is_active=True)
        return section.get_permission_codename(action)
    except (Section.DoesNotExist, Exception):
        # Fallback to default format if section doesn't exist or table doesn't exist
        return f'{action}_{section_name}'


def user_has_section_permission(user, section_name, action):
    """
    Check if a user has a specific section permission.
    
    Args:
        user: User object
        section_name: Name of the section (e.g., 'users', 'locations')
        action: Permission action ('view', 'add', 'change', 'delete')
    
    Returns:
        True if user has permission, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Get permission codename
    codename = get_section_permission(section_name, action)
    
    # Get ContentType for Section model
    try:
        section_content_type = ContentType.objects.get_for_model(Section)
        
        # Try to get the permission object
        try:
            permission = Permission.objects.get(
                codename=codename,
                content_type=section_content_type
            )
        except Permission.DoesNotExist:
            # Permission doesn't exist - return False
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Permission {codename} does not exist for section {section_name}')
            return False
        
        # Check directly via groups (more reliable than has_perm which can be cached)
        # Refresh user groups to ensure we have the latest data
        # Use select_related and prefetch_related for optimal query performance
        user_groups = user.groups.select_related().prefetch_related('permissions')
        for group in user_groups:
            # Check if this group has the permission by checking permission IDs
            # This is more reliable than checking codenames
            if group.permissions.filter(id=permission.id).exists():
                return True
        
        # Also check if user has permission directly assigned (not via group)
        if user.user_permissions.filter(id=permission.id).exists():
            return True
        
        # Fallback: Use Django's has_perm (may be cached, but should work)
        # Note: Django caches permissions per request, so this might not reflect
        # recent changes until the user's session is refreshed
        try:
            has_perm = user.has_perm(f'hotel_app.{codename}')
            if has_perm:
                return True
        except Exception:
            # If has_perm fails for any reason, we've already checked groups above
            pass
        
        return False
        
    except (ContentType.DoesNotExist, Exception) as e:
        # If permission doesn't exist or table doesn't exist, deny access
        # This handles cases where migrations haven't been run yet
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error checking permission {codename} for section {section_name}: {str(e)}')
        return False


def require_section_permission(section_name, action):
    """
    Decorator for function-based views to require a section permission.
    
    Usage:
        @require_section_permission('users', 'view')
        def my_view(request):
            ...
    
    Args:
        section_name: Name of the section (e.g., 'users', 'locations')
        action: Permission action ('view', 'add', 'change', 'delete')
    
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not user_has_section_permission(request.user, section_name, action):
                from django.shortcuts import render
                from django.http import HttpResponseForbidden
                
                # Render custom permission denied page
                context = {
                    'section_name': section_name,
                    'permission_action': action,
                    'user': request.user,
                }
                return render(
                    request, 
                    'dashboard/permission_denied.html', 
                    context,
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_section_permissions(section_name, actions):
    """
    Decorator for function-based views to require multiple section permissions.
    User needs at least one of the specified permissions.
    
    Usage:
        @require_section_permissions('users', ['view', 'add'])
        def my_view(request):
            ...
    
    Args:
        section_name: Name of the section (e.g., 'users', 'locations')
        actions: List of permission actions (e.g., ['view', 'add'])
    
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            has_permission = any(
                user_has_section_permission(request.user, section_name, action)
                for action in actions
            )
            if not has_permission:
                from django.shortcuts import render
                from django.http import HttpResponseForbidden
                
                # Render custom permission denied page
                context = {
                    'section_name': section_name,
                    'permission_action': ', '.join(actions),
                    'user': request.user,
                }
                return render(
                    request, 
                    'dashboard/permission_denied.html', 
                    context,
                    status=403
                )
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class SectionPermissionRequiredMixin(AccessMixin):
    """
    Mixin for class-based views to require a section permission.
    
    Usage:
        class MyView(SectionPermissionRequiredMixin, ListView):
            section_name = 'users'
            permission_action = 'view'
            ...
    """
    section_name = None
    permission_action = 'view'
    permission_denied_message = "You don't have permission to access this section."
    
    def dispatch(self, request, *args, **kwargs):
        if not self.section_name:
            raise ValueError(
                "SectionPermissionRequiredMixin requires 'section_name' to be set."
            )
        
        if not user_has_section_permission(
            request.user, 
            self.section_name, 
            self.permission_action
        ):
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        """Handle permission denied."""
        from django.shortcuts import render
        from django.http import HttpResponseForbidden
        
        # Render custom permission denied page
        context = {
            'section_name': self.section_name,
            'permission_action': self.permission_action,
            'user': self.request.user,
        }
        return render(
            self.request, 
            'dashboard/permission_denied.html', 
            context,
            status=403
        )


class SectionPermissionMultipleMixin(AccessMixin):
    """
    Mixin for class-based views to require at least one of multiple section permissions.
    
    Usage:
        class MyView(SectionPermissionMultipleMixin, ListView):
            section_name = 'users'
            permission_actions = ['view', 'add']
            ...
    """
    section_name = None
    permission_actions = ['view']
    permission_denied_message = "You don't have permission to access this section."
    
    def dispatch(self, request, *args, **kwargs):
        if not self.section_name:
            raise ValueError(
                "SectionPermissionMultipleMixin requires 'section_name' to be set."
            )
        
        has_permission = any(
            user_has_section_permission(request.user, self.section_name, action)
            for action in self.permission_actions
        )
        
        if not has_permission:
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        """Handle permission denied."""
        from django.shortcuts import render
        from django.http import HttpResponseForbidden
        
        # Render custom permission denied page
        context = {
            'section_name': self.section_name,
            'permission_action': ', '.join(self.permission_actions),
            'user': self.request.user,
        }
        return render(
            self.request, 
            'dashboard/permission_denied.html', 
            context,
            status=403
        )


def check_section_permission(user, section_name, action):
    """
    Utility function to check section permission (can be used in templates via context).
    
    Args:
        user: User object
        section_name: Name of the section (e.g., 'users', 'locations')
        action: Permission action ('view', 'add', 'change', 'delete')
    
    Returns:
        True if user has permission, False otherwise
    """
    return user_has_section_permission(user, section_name, action)

