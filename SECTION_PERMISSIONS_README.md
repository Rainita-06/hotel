# Section-Based Permissions System

This document describes the role-based permissions system where permissions are tied to sidebar sections and managed through Django's auth.Group system.

## Overview

The system implements section-based permissions where:
- Each sidebar section (users, locations, tickets, etc.) has CRUD permissions (view, add, change, delete)
- User profiles map to Django auth.Group
- Permissions are assigned to Groups, and users inherit permissions through group membership
- UserProfile.role automatically syncs with Group membership

## Architecture

### Models

1. **Section Model** (`hotel_app/models.py`)
   - Represents sidebar sections (users, locations, tickets, etc.)
   - Each section has a name, display_name, description, and is_active flag
   - Provides methods to get permission codenames

2. **UserProfile Model** (`hotel_app/models.py`)
   - Has a `role` field that maps to Django Groups
   - Role values: 'admin', 'staff', 'user'
   - Automatically synced with Group membership via signals

### Signals

1. **sync_userprofile_to_group** (`hotel_app/signals.py`)
   - Syncs UserProfile.role to Django Group membership
   - When a UserProfile's role changes, the user is added/removed from the corresponding Group

2. **sync_user_groups_to_profile** (`hotel_app/signals.py`)
   - Syncs Django Group membership back to UserProfile.role
   - Handles cases where groups are changed directly (e.g., via admin)

### Permission System

1. **Section Permissions** (`hotel_app/section_permissions.py`)
   - Functions to check section permissions
   - Decorators for function-based views
   - Mixins for class-based views

2. **Template Tags** (`hotel_app/templatetags/section_permissions.py`)
   - `has_section_permission` filter for templates
   - `check_section_permission` tag for templates

3. **Context Processor** (`hotel_app/context_processors.py`)
   - Provides `section_permissions` context variable
   - Contains permission checks for all sections

### Management Command

**create_section_permissions** (`hotel_app/management/commands/create_section_permissions.py`)
- Creates Section instances for all sidebar sections
- Creates Django Permissions for each section (view, add, change, delete)
- Usage: `python manage.py create_section_permissions`

## Setup Instructions

### 1. Create Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Sections and Permissions

```bash
python manage.py create_section_permissions
```

This will:
- Create Section instances for all sidebar sections
- Create Django Permissions for each section with CRUD operations

### 3. Assign Permissions to Groups

Permissions are assigned to Groups through the "Manage Users" → "User Profiles" interface, or programmatically:

```python
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section

# Get section and permissions
section = Section.objects.get(name='users')
section_content_type = ContentType.objects.get_for_model(Section)

# Get permission
view_permission = Permission.objects.get(
    codename=section.get_permission_codename('view'),
    content_type=section_content_type
)

# Assign to group
admin_group = Group.objects.get(name='Admins')
admin_group.permissions.add(view_permission)
```

### 4. Sync Existing Users

If you have existing users, sync their UserProfile roles with Groups:

```python
from hotel_app.models import UserProfile
from hotel_app.signals import sync_userprofile_to_group

# Sync all user profiles
for profile in UserProfile.objects.all():
    sync_userprofile_to_group(sender=UserProfile, instance=profile, created=False)
```

## Usage

### In Views

#### Function-Based Views

```python
from hotel_app.section_permissions import require_section_permission

@require_section_permission('users', 'view')
def my_view(request):
    # User must have users.view permission
    ...
```

#### Class-Based Views

```python
from hotel_app.section_permissions import SectionPermissionRequiredMixin
from django.views.generic import ListView

class MyView(SectionPermissionRequiredMixin, ListView):
    section_name = 'users'
    permission_action = 'view'
    ...
```

### In Templates

```django
{% load section_permissions %}

{% if user|has_section_permission:'users.view' %}
    <!-- User can view users section -->
{% endif %}

{% if user|has_section_permission:'users.add' %}
    <!-- User can add users -->
{% endif %}

{% if user|has_section_permission:'users.change' %}
    <!-- User can change users -->
{% endif %}

{% if user|has_section_permission:'users.delete' %}
    <!-- User can delete users -->
{% endif %}
```

### In APIs

```python
from hotel_app.section_permissions import user_has_section_permission

def my_api_view(request):
    if not user_has_section_permission(request.user, 'users', 'view'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    ...
```

## Sidebar Sections

The following sections are defined:

- `users` - Manage Users
- `locations` - Locations management
- `tickets` - Service Requests/Tickets
- `requests` - Predefined Requests
- `sla` - SLA Configuration
- `messaging` - Messaging Setup
- `gym` - Gym Management
- `integrations` - Integrations
- `analytics` - Analytics
- `performance` - Performance Dashboard
- `feedback` - Feedback/Reviews
- `breakfast_voucher` - Breakfast Voucher
- `dashboard` - Dashboard overview

## Permission Actions

Each section has four permission actions:

- `view` - Can view the section
- `add` - Can add new items in the section
- `change` - Can modify items in the section
- `delete` - Can delete items in the section

## Group to Role Mapping

UserProfile roles map to Django Groups as follows:

- `admin` → `Admins` group
- `staff` → `Staff` group
- `user` → `Users` group

## API Endpoints

### Get Group Permissions

```
GET /dashboard/api/groups/<group_id>/permissions/
```

Returns JSON with group permissions organized by section.

### Update Group Permissions

```
POST /dashboard/api/groups/<group_id>/permissions/update/
```

Request body:
```json
{
    "permissions_by_section": {
        "users": {
            "view": true,
            "add": true,
            "change": true,
            "delete": false
        },
        "locations": {
            "view": true,
            "add": false,
            "change": false,
            "delete": false
        }
    }
}
```

## Testing

Run the section permissions tests:

```bash
python manage.py test hotel_app.tests_section_permissions
```

Tests cover:
- Permission creation
- Permission checking
- UserProfile ↔ Group syncing
- View decorators and mixins
- Template tags
- API endpoints

## Troubleshooting

### Permissions not working

1. Ensure sections and permissions are created:
   ```bash
   python manage.py create_section_permissions
   ```

2. Check that permissions are assigned to groups:
   - Go to "Manage Users" → "User Profiles"
   - Click "Edit" on a group
   - Ensure permissions are checked

3. Verify user is in the correct group:
   ```python
   user.groups.all()  # Should show the group
   ```

4. Check that UserProfile.role matches group membership:
   ```python
   user.userprofile.role  # Should match group name
   ```

### Signal not syncing

1. Check that signals are registered in `hotel_app/apps.py`:
   ```python
   class HotelAppConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'hotel_app'
       
       def ready(self):
           import hotel_app.signals  # Ensure signals are imported
   ```

2. Check signal logs for errors:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```

## Future Enhancements

- Add permission inheritance (e.g., change implies view)
- Add custom permission types beyond CRUD
- Add permission caching for performance
- Add permission audit logging
- Add bulk permission assignment

## Files Modified/Created

### Created Files
- `hotel_app/models.py` - Added Section model
- `hotel_app/section_permissions.py` - Permission checking functions, decorators, mixins
- `hotel_app/templatetags/section_permissions.py` - Template tags
- `hotel_app/management/commands/create_section_permissions.py` - Management command
- `hotel_app/tests_section_permissions.py` - Unit tests
- `SECTION_PERMISSIONS_README.md` - This file

### Modified Files
- `hotel_app/signals.py` - Added UserProfile ↔ Group sync signals
- `hotel_app/context_processors.py` - Added section_permissions context
- `hotel_app/dashboard_views.py` - Updated manage_users_profiles and API views
- `hotel_app/admin.py` - Registered Section model
- `templates/dashboard/components/sidebar.html` - Updated to use section permissions

## Migration

To apply the Section model migration:

```bash
python manage.py makemigrations hotel_app
python manage.py migrate hotel_app
```

Then create sections and permissions:

```bash
python manage.py create_section_permissions
```

## Example: Assigning Permissions to a Group

```python
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section

# Get section
section = Section.objects.get(name='users')
section_content_type = ContentType.objects.get_for_model(Section)

# Get group
admin_group = Group.objects.get(name='Admins')

# Assign all permissions for users section
for action in ['view', 'add', 'change', 'delete']:
    codename = section.get_permission_codename(action)
    permission = Permission.objects.get(
        codename=codename,
        content_type=section_content_type
    )
    admin_group.permissions.add(permission)
```

## Example: Checking Permissions in a View

```python
from hotel_app.section_permissions import user_has_section_permission
from django.http import JsonResponse

def my_view(request):
    if not user_has_section_permission(request.user, 'users', 'view'):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # User has permission, proceed
    ...
```

## Example: Using in Templates

```django
{% load section_permissions %}

<div class="sidebar">
    {% if user|has_section_permission:'users.view' %}
        <a href="{% url 'dashboard:manage_users' %}">Users</a>
    {% endif %}
    
    {% if user|has_section_permission:'locations.view' %}
        <a href="{% url 'dashboard:locations' %}">Locations</a>
    {% endif %}
</div>

{% if user|has_section_permission:'users.add' %}
    <button onclick="addUser()">Add User</button>
{% endif %}
```

