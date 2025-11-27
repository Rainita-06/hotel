"""
Template tags for section-based permissions.

Usage in templates:
    {% load section_permissions %}
    {% if user|has_section_permission:'users.view' %}
        ...
    {% endif %}
"""
from django import template
from hotel_app.section_permissions import user_has_section_permission

register = template.Library()


@register.filter
def has_section_permission(user, permission_string):
    """
    Check if user has a section permission.
    
    Usage:
        {% if user|has_section_permission:'users.view' %}
        {% if user|has_section_permission:'locations.add' %}
    
    Args:
        user: User object
        permission_string: Permission string in format 'section.action' (e.g., 'users.view')
    
    Returns:
        True if user has permission, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    try:
        section_name, action = permission_string.split('.')
        # Refresh user from database to get latest groups and permissions
        # This ensures we're not using cached data
        from django.contrib.auth.models import User
        try:
            # Get fresh user object with groups and permissions
            fresh_user = User.objects.prefetch_related('groups__permissions', 'user_permissions').get(pk=user.pk)
            return user_has_section_permission(fresh_user, section_name, action)
        except User.DoesNotExist:
            # If user doesn't exist, fallback to original user object
            return user_has_section_permission(user, section_name, action)
    except (ValueError, AttributeError, Exception) as e:
        # Return False if there's any error (e.g., Section table doesn't exist)
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f'Error checking permission {permission_string} for user {user}: {str(e)}')
        return False


@register.simple_tag
def check_section_permission(user, section_name, action):
    """
    Check if user has a section permission (simple tag version).
    
    Usage:
        {% check_section_permission user 'users' 'view' as can_view_users %}
        {% if can_view_users %}
            ...
        {% endif %}
    
    Args:
        user: User object
        section_name: Name of the section (e.g., 'users', 'locations')
        action: Permission action ('view', 'add', 'change', 'delete')
    
    Returns:
        True if user has permission, False otherwise
    """
    return user_has_section_permission(user, section_name, action)


@register.inclusion_tag('dashboard/components/sidebar_link.html', takes_context=True)
def sidebar_link(context, section_name, url_name, display_name, icon_path=None, active_icon_path=None):
    """
    Render a sidebar link if user has permission to view the section.
    
    Usage:
        {% sidebar_link 'users' 'dashboard:manage_users' 'Users' %}
    
    Args:
        section_name: Name of the section (e.g., 'users', 'locations')
        url_name: URL name to link to
        display_name: Display name for the link
        icon_path: Path to icon (optional)
        active_icon_path: Path to active icon (optional)
    
    Returns:
        Dictionary with link data if user has permission, None otherwise
    """
    user = context.get('user')
    
    if not user_has_section_permission(user, section_name, 'view'):
        return None
    
    request = context.get('request')
    is_active = False
    if request:
        # Check if current URL matches
        try:
            from django.urls import reverse, resolve
            current_url = resolve(request.path).url_name
            if url_name == current_url or request.resolver_match.view_name == url_name:
                is_active = True
        except Exception:
            pass
    
    return {
        'url_name': url_name,
        'display_name': display_name,
        'icon_path': icon_path,
        'active_icon_path': active_icon_path or icon_path,
        'is_active': is_active,
    }

