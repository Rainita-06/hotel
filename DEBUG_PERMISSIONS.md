# Debugging Permission Issues

## Issue 1: 403 Error on `/dashboard/manage-users/profiles/`

### Problem
When accessing `/dashboard/manage-users/profiles/`, you get a 403 error even after assigning `users.view` permission.

### Root Cause
The error is coming from the `require_role` decorator which was raising a `PermissionDenied` exception instead of showing the custom permission denied page.

### Solution Applied
1. Updated `require_role` decorator to render custom permission denied page
2. Updated `require_permission` decorator to render custom permission denied page
3. Both decorators now show the friendly error page instead of raising exceptions

### How to Verify
1. Make sure the user has `users.view` permission assigned to their group
2. Access `/dashboard/manage-users/profiles/` directly
3. You should see the custom permission denied page (not a 403 error)
4. If permission is granted, the page should load normally

## Issue 2: Feedback Section Not Visible in Sidebar

### Problem
User has `feedback.view` permission but the Feedback section doesn't appear in the sidebar.

### Root Cause
1. The `feedback_inbox` view was using `@user_passes_test(is_staff)` instead of `@require_section_permission('feedback', 'view')`
2. The sidebar checks `user|has_section_permission:'feedback.view'` which might not be working correctly

### Solution Applied
1. Updated `feedback_inbox` to use `@require_section_permission('feedback', 'view')`
2. Updated `feedback_detail` to use `@require_section_permission('feedback', 'view')`
3. Verified sidebar template uses correct permission check

### How to Verify
1. Assign `feedback.view` permission to user's group
2. Logout and login as the user
3. Check sidebar - Feedback section should be visible
4. Access `/dashboard/feedback/` - should load normally
5. If permission is missing, should see permission denied page

## Debugging Steps

### Step 1: Verify Permissions in Database
```bash
python manage.py verify_user_permissions <username>
```

This will show:
- User's groups
- All section permissions
- Which groups grant each permission

### Step 2: Check Permission Assignment
1. Login as superuser
2. Go to **Manage Users → User Profiles**
3. Click **Edit** on the user's group
4. Verify `feedback.view` is checked
5. Click **Save Permissions**
6. Verify permissions are saved

### Step 3: Verify User Group Assignment
1. Go to **Manage Users → All Users**
2. Click on the user
3. Verify user is assigned to the correct group
4. Save if needed

### Step 4: Clear Cache and Reload
1. Logout from the test user account
2. Clear browser cache (Ctrl+Shift+Delete)
3. Login again as test user
4. Check sidebar and page access

### Step 5: Check Permission Check Logic
```python
# Run in Django shell
from django.contrib.auth.models import User
from hotel_app.section_permissions import user_has_section_permission

user = User.objects.get(username='your_username')
print(f"Has feedback.view: {user_has_section_permission(user, 'feedback', 'view')}")
print(f"Has users.view: {user_has_section_permission(user, 'users', 'view')}")
```

## Common Issues

### Issue: Permission Not Showing After Assignment
**Solution:**
- Logout and login again
- Clear browser cache
- Verify permission is actually saved in database
- Check that user is in the correct group

### Issue: Sidebar Not Updating
**Solution:**
- Sidebar is rendered server-side, so changes should reflect immediately
- If not, clear browser cache
- Check that template tag is working: `{% if user|has_section_permission:'feedback.view' %}`

### Issue: 403 Error Instead of Custom Page
**Solution:**
- Verify decorators are updated to render custom page
- Check that `permission_denied.html` template exists
- Verify no middleware is intercepting the response

## Testing Checklist

- [ ] User has correct group assignment
- [ ] Group has correct permissions assigned
- [ ] Permissions are saved in database
- [ ] User logged out and logged back in
- [ ] Browser cache cleared
- [ ] Sidebar shows correct sections
- [ ] Page access works correctly
- [ ] Permission denied page shows correctly
- [ ] No 403 errors in console

## Quick Fixes

### Fix 1: Reassign User to Group
```python
from django.contrib.auth.models import User, Group

user = User.objects.get(username='username')
group = Group.objects.get(name='Group Name')
user.groups.add(group)
user.save()
```

### Fix 2: Manually Assign Permission
```python
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section

user = User.objects.get(username='username')
group = Group.objects.get(name='Group Name')

section = Section.objects.get(name='feedback')
section_ct = ContentType.objects.get_for_model(Section)
permission = Permission.objects.get(
    codename='view_feedback',
    content_type=section_ct
)

group.permissions.add(permission)
user.groups.add(group)
```

### Fix 3: Verify Permission Check
```python
from hotel_app.section_permissions import user_has_section_permission
from django.contrib.auth.models import User

user = User.objects.get(username='username')
# This should return True if permission is correctly assigned
print(user_has_section_permission(user, 'feedback', 'view'))
```

