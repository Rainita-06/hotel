"""
Role-Based Access Control (RBAC) Services for the hotel management system.
This module provides functions to manage user roles, permissions, and access control.
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import UserProfile

User = get_user_model()


# Define role permissions mapping
ROLE_PERMISSIONS = {
    'admin': {
        'dashboard': ['view', 'add', 'change', 'delete'],
        'users': ['view', 'add', 'change', 'delete'],
        'departments': ['view', 'add', 'change', 'delete'],
        'locations': ['view', 'add', 'change', 'delete'],
        'tickets': ['view', 'add', 'change', 'delete'],
        'requests': ['view', 'add', 'change', 'delete'],
        'vouchers': ['view', 'add', 'change', 'delete'],
        'gym': ['view', 'add', 'change', 'delete'],
        'feedback': ['view', 'add', 'change', 'delete'],
        'analytics': ['view', 'add', 'change', 'delete'],
        'reports': ['view', 'add', 'change', 'delete'],
        'settings': ['view', 'add', 'change', 'delete'],
        'sla': ['view', 'add', 'change', 'delete'],
        'messaging': ['view', 'add', 'change', 'delete'],
        'integrations': ['view', 'add', 'change', 'delete'],
        'performance': ['view', 'add', 'change', 'delete'],
    },
    'staff': {
        'dashboard': ['view'],
        'users': ['view'],
        'departments': ['view'],
        'locations': ['view'],
        'tickets': ['view', 'add', 'change'],  # Staff can view and modify tickets
        'requests': ['view'],
        'vouchers': ['view', 'add', 'change'],
        'gym': ['view', 'add', 'change'],
        'feedback': ['view', 'add', 'change'],
        'analytics': ['view'],
        'reports': ['view'],
        'settings': ['view'],
        'sla': ['view'],
        'messaging': ['view', 'add', 'change'],
        'integrations': ['view'],
        'performance': ['view'],
    },
    'user': {
        'dashboard': ['view'],
        'tickets': ['view', 'add'],  # Regular users can only view and create tickets
        'requests': ['view'],
        'feedback': ['view', 'add'],
        'profile': ['view', 'change'],  # Users can view and edit their own profile
    }
}


def get_model_permissions(model_class, actions):
    """
    Get permissions for a specific model and actions.
    
    Args:
        model_class: Django model class
        actions: List of actions (view, add, change, delete)
        
    Returns:
        List of Permission objects
    """
    ct = ContentType.objects.get_for_model(model_class)
    permissions = []
    
    for action in actions:
        try:
            perm = Permission.objects.get(
                codename=f"{action}_{model_class._meta.model_name}",
                content_type=ct
            )
            permissions.append(perm)
        except Exception:
            # Skip if permission doesn't exist
            pass
            
    return permissions


def ensure_groups_and_permissions():
    """
    Ensure that all required groups and their permissions exist.
    This function should be called during application startup or in migrations.
    """
    # Create or get groups
    admin_group, _ = Group.objects.get_or_create(name='Admins')
    staff_group, _ = Group.objects.get_or_create(name='Staff')
    user_group, _ = Group.objects.get_or_create(name='Users')
    
    # Assign permissions to groups based on ROLE_PERMISSIONS mapping
    # For simplicity, we're using a basic approach here
    # In a real application, you would map these to actual model permissions
    
    # Admin group gets all permissions
    # Staff group gets operational permissions
    # User group gets limited permissions
    
    return admin_group, staff_group, user_group


def assign_user_to_role(user, role_name):
    """
    Assign a user to a specific role.
    
    Args:
        user: User object
        role_name: Role name (admin, staff, user)
    """
    try:
        group = Group.objects.get(name=f"{role_name.capitalize()}s")
        user.groups.clear()  # Remove from all other groups
        user.groups.add(group)
        
        # Update user profile role if it exists
        try:
            profile = user.userprofile
            profile.role = role_name
            profile.save(update_fields=['role'])
        except Exception:
            pass
            
        return True
    except Exception:
        return False


def get_user_permissions(user):
    """
    Get all permissions for a user based on their groups.
    
    Args:
        user: User object
        
    Returns:
        Set of permission codenames
    """
    permissions = set()
    
    # Get permissions from all groups the user belongs to
    for group in user.groups.all():
        for perm in group.permissions.all():
            permissions.add(perm.codename)
            
    return permissions


def has_permission(user, permission_codename):
    """
    Check if a user has a specific permission.
    
    Args:
        user: User object
        permission_codename: Permission codename (e.g., 'view_ticket')
        
    Returns:
        Boolean indicating if user has permission
    """
    return user.has_perm(permission_codename)


def get_user_role(user):
    """
    Get the role of a user based on their groups.
    
    Args:
        user: User object
        
    Returns:
        String representing user role (admin, staff, user) or None
    """
    group_names = [group.name.lower() for group in user.groups.all()]
    
    if 'admins' in group_names:
        return 'admin'
    elif 'staff' in group_names:
        return 'staff'
    elif 'users' in group_names:
        return 'user'
    else:
        return None


def can_access_section(user, section_name):
    """
    Check if a user can access a specific section of the application.
    
    Args:
        user: User object
        section_name: Name of the section (e.g., 'dashboard', 'tickets', 'sla')
        
    Returns:
        Boolean indicating if user can access the section
    """
    role = get_user_role(user)
    if not role:
        return False
        
    # Admins can access everything
    if role == 'admin':
        return True
        
    # Check if the role has permissions for this section
    if section_name in ROLE_PERMISSIONS.get(role, {}):
        return True
        
    return False


def get_accessible_sections(user):
    """
    Get all sections that a user can access.
    
    Args:
        user: User object
        
    Returns:
        List of section names that the user can access
    """
    role = get_user_role(user)
    if not role:
        return []
        
    # Admins can access everything
    if role == 'admin':
        # Return all sections
        all_sections = set()
        for role_permissions in ROLE_PERMISSIONS.values():
            all_sections.update(role_permissions.keys())
        return list(all_sections)
        
    # Return sections for the user's role
    return list(ROLE_PERMISSIONS.get(role, {}).keys())