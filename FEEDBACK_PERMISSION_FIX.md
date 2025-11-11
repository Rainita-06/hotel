# Fix for Feedback Permission Not Showing in Sidebar

## Problem
User has feedback permission assigned to their group, but the Feedback section is not visible in the sidebar.

## Root Causes
1. **Permission Cache**: Django caches permissions, and the cache might not be refreshed after assigning permissions
2. **Permission Check Logic**: The previous logic relied on `user.has_perm()` which uses Django's cached permissions
3. **User Not in Group**: User might not be assigned to the group that has the permission
4. **Permission Not Assigned**: Permission might not be correctly assigned to the group

## Fix Applied

### 1. Improved Permission Check Logic
Updated `user_has_section_permission()` in `hotel_app/section_permissions.py` to:
- Check permissions directly via groups (more reliable)
- Use `prefetch_related('permissions')` to optimize database queries
- Check user permissions directly assigned (not just via groups)
- Fallback to Django's `has_perm()` only if needed

### 2. Created Debug Command
Created `check_feedback_permission` command to help debug permission issues:
```bash
python manage.py check_feedback_permission <username>
```

## How to Verify and Fix

### Step 1: Check User's Permission
```bash
python manage.py check_feedback_permission <username>
```

This will show:
- User's groups
- Which groups have feedback.view permission
- Whether user is in those groups
- Permission check result

### Step 2: Verify Group Assignment
1. Login as superuser
2. Go to **Manage Users → All Users**
3. Click on the user
4. Verify the user is assigned to the correct group
5. Save if needed

### Step 3: Verify Permission Assignment
1. Go to **Manage Users → User Profiles**
2. Click **Edit** on the group that should have feedback permission
3. Verify `feedback.view` is checked
4. Click **Save Permissions**
5. Verify permissions are saved

### Step 4: Clear Cache and Reload
1. **Logout** from the test user account
2. **Clear browser cache** (Ctrl+Shift+Delete)
3. **Login again** as test user
4. Check sidebar - Feedback section should be visible

### Step 5: If Still Not Working
Run the debug command and check:
1. Is the user in the correct group?
2. Does the group have feedback.view permission?
3. Is the permission correctly assigned?

## Quick Fix Script
```python
# Run in Django shell: python manage.py shell

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section
from hotel_app.section_permissions import user_has_section_permission

# Get user and group
user = User.objects.get(username='your_username')
group = Group.objects.get(name='your_group_name')

# Get feedback permission
section = Section.objects.get(name='feedback')
section_ct = ContentType.objects.get_for_model(Section)
permission = Permission.objects.get(
    codename='view_feedback',
    content_type=section_ct
)

# Assign permission to group
group.permissions.add(permission)

# Assign user to group
user.groups.add(group)

# Verify
print(f"User has feedback.view: {user_has_section_permission(user, 'feedback', 'view')}")
```

## Testing
1. Assign feedback.view permission to a group
2. Assign a user to that group
3. Logout and login as that user
4. Check sidebar - Feedback section should be visible
5. Click on Feedback - should load the feedback page

## Notes
- Permissions are checked on every request
- Sidebar is rendered server-side, so permissions are enforced immediately
- User must logout and login again after permission changes
- Browser cache should be cleared for best results
- Superusers have all permissions automatically

