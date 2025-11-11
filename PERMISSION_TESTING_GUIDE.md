# Permission System Testing Guide

This guide explains how to test the section-based permission system to ensure permissions are properly enforced in both the sidebar and page access.

## Prerequisites

1. **Create Sections and Permissions**
   ```bash
   python manage.py create_section_permissions
   ```

2. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## Testing Steps

### Step 1: Create Test Users and Groups

1. **Login as Superuser** (has all permissions by default)

2. **Create Test Groups (User Profiles)**
   - Go to: **Manage Users → User Profiles**
   - Click **"Create Profile"**
   - Create profiles like:
     - `Limited User` - Limited permissions
     - `Staff Member` - Staff-level permissions
     - `Manager` - Manager-level permissions

### Step 2: Assign Permissions to Groups

1. **Navigate to User Profiles**
   - Go to: **Manage Users → User Profiles**

2. **Edit Permissions for a Group**
   - Click the **Edit** button (pencil icon) on a group card
   - In the modal, toggle permissions for different sections:
     - **Users**: View, Add, Change, Delete
     - **Locations**: View, Add, Change, Delete
     - **Tickets**: View, Add, Change, Delete
     - **Analytics**: View, Add, Change, Delete
     - etc.

3. **Save Permissions**
   - Click **"Save Permissions"**
   - Verify the permissions are saved successfully

### Step 3: Assign Users to Groups

1. **Go to User Management**
   - Navigate to: **Manage Users → All Users**

2. **Edit a User**
   - Click on a user to edit
   - Assign the user to a group (profile) with limited permissions
   - Save the user

### Step 4: Test Sidebar Visibility

1. **Logout and Login as Test User**
   - Logout from superuser account
   - Login as the test user you assigned to a limited group

2. **Check Sidebar**
   - The sidebar should only show sections the user has `view` permission for
   - Sections without `view` permission should NOT appear in the sidebar
   - Verify the following:
     - ✅ Sections with permission are visible
     - ✅ Sections without permission are hidden
     - ✅ Menu items appear/disappear based on permissions

3. **Test Different Permission Levels**
   - Create users with different permission sets
   - Verify sidebar shows/hides sections correctly for each user

### Step 5: Test Page Access Restrictions

1. **Try Accessing Restricted Pages Directly**
   - While logged in as a user without permissions, try accessing:
     - `/dashboard/manage-users/` (Users section)
     - `/dashboard/locations/` (Locations section)
     - `/dashboard/tickets/` (Tickets section)
     - `/dashboard/analytics/` (Analytics section)
     - etc.

2. **Verify Permission Denied Page**
   - You should see a custom **"Access Denied"** page
   - The page should display:
     - ✅ Clear error message
     - ✅ Required permission information
     - ✅ "Go to Dashboard" button
     - ✅ "Go Back" button
     - ✅ Contact information for requesting access

3. **Test with Different URLs**
   - Try accessing pages via direct URL
   - Try accessing pages via navigation (if somehow accessible)
   - Verify all restricted pages show the permission denied page

### Step 6: Test Permission Toggles

1. **Update Permissions in Real-Time**
   - As superuser, go to **User Profiles**
   - Edit a group's permissions
   - Remove `view` permission for a section (e.g., remove `users.view`)
   - Save the changes

2. **Test Immediate Effect**
   - Logout and login as a user in that group
   - Verify:
     - ✅ Sidebar no longer shows the removed section
     - ✅ Direct URL access shows permission denied page
     - ✅ User cannot access the section in any way

3. **Re-add Permissions**
   - As superuser, re-add the permission
   - Logout and login as test user again
   - Verify:
     - ✅ Sidebar shows the section again
     - ✅ User can access the page
     - ✅ All functionality works correctly

### Step 7: Test CRUD Permissions

1. **Test View Permission**
   - User with `view` permission should:
     - ✅ See the section in sidebar
     - ✅ Access the page
     - ✅ View data
     - ❌ NOT see "Create", "Edit", "Delete" buttons

2. **Test Add Permission**
   - User with `add` permission should:
     - ✅ See "Create" buttons
     - ✅ Access create forms
     - ❌ NOT see "Edit" or "Delete" buttons (without `change`/`delete`)

3. **Test Change Permission**
   - User with `change` permission should:
     - ✅ See "Edit" buttons
     - ✅ Access edit forms
     - ✅ Update data
     - ❌ NOT see "Delete" buttons (without `delete`)

4. **Test Delete Permission**
   - User with `delete` permission should:
     - ✅ See "Delete" buttons
     - ✅ Delete records
     - ✅ Access delete confirmations

### Step 8: Test Superuser Access

1. **Superuser Should Have All Permissions**
   - Login as superuser
   - Verify:
     - ✅ All sections visible in sidebar
     - ✅ Can access all pages
     - ✅ Can perform all actions (Create, Edit, Delete)
     - ✅ No permission denied pages

### Step 9: Test Edge Cases

1. **User with No Permissions**
   - Create a user with no group assignments
   - Verify:
     - ✅ Only Dashboard is visible
     - ✅ All other sections are hidden
     - ✅ Accessing any section shows permission denied

2. **User with Multiple Groups**
   - Assign user to multiple groups
   - Verify:
     - ✅ User has union of all permissions (if any group has permission, user has it)
     - ✅ Sidebar shows all sections user has access to
     - ✅ User can access all permitted pages

3. **Permission Removal While User is Logged In**
   - While user is on a page, remove their permission as superuser
   - User tries to navigate or refresh
   - Verify:
     - ✅ Permission denied page is shown
     - ✅ Sidebar updates on next page load

## Expected Behavior Summary

### Sidebar Behavior
- ✅ Sections with `view` permission: **Visible**
- ❌ Sections without `view` permission: **Hidden**
- ✅ Dashboard: **Always visible** (unless you want to restrict it)

### Page Access Behavior
- ✅ User has permission: **Page loads normally**
- ❌ User lacks permission: **Custom "Access Denied" page shown**
- ✅ Superuser: **Access to all pages**

### Button/Action Visibility
- ✅ `view` permission: **View page, see data**
- ✅ `add` permission: **See "Create" buttons**
- ✅ `change` permission: **See "Edit" buttons**
- ✅ `delete` permission: **See "Delete" buttons**

## Troubleshooting

### Sidebar Not Updating
- **Clear browser cache** and reload
- **Logout and login again** to refresh permissions
- Check browser console for JavaScript errors

### Permission Denied Page Not Showing
- Verify `permission_denied.html` template exists
- Check that views use `@require_section_permission` decorator
- Verify permissions are correctly assigned to groups

### Permissions Not Working
- Run `python manage.py create_section_permissions` again
- Check database for Section and Permission records
- Verify user is assigned to correct group
- Check that group has correct permissions assigned

### Testing Checklist

- [ ] Created test users and groups
- [ ] Assigned permissions to groups
- [ ] Assigned users to groups
- [ ] Tested sidebar visibility
- [ ] Tested page access restrictions
- [ ] Tested permission denied page
- [ ] Tested permission toggles
- [ ] Tested CRUD permissions
- [ ] Tested superuser access
- [ ] Tested edge cases

## Quick Test Script

```python
# Run this in Django shell: python manage.py shell

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section

# Create a test user
user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')

# Create a test group
group = Group.objects.create(name='Test Group')

# Get a section permission
section = Section.objects.get(name='users')
content_type = ContentType.objects.get_for_model(Section)
permission = Permission.objects.get(
    codename='view_users',
    content_type=content_type
)

# Assign permission to group
group.permissions.add(permission)

# Assign user to group
user.groups.add(group)

# Test permission
from hotel_app.section_permissions import user_has_section_permission
print(f"User has users.view: {user_has_section_permission(user, 'users', 'view')}")
print(f"User has users.add: {user_has_section_permission(user, 'users', 'add')}")
```

## Notes

- Permissions are checked on every request
- Sidebar is rendered server-side, so permissions are enforced immediately
- Permission denied page is shown for all restricted access attempts
- Superusers bypass all permission checks
- Permissions are cached by Django, but changes should reflect immediately on next request

