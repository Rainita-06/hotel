# Fixes Applied for Permission Issues

## Issues Fixed

### 1. 403 Error on `/dashboard/manage-users/profiles/`

**Problem:** Getting 403 error even after assigning `users.view` permission.

**Root Cause:** 
- The `require_role` decorator was raising `PermissionDenied` exception instead of rendering the custom permission denied page
- The error was being caught by Django's default error handler

**Fix Applied:**
- Updated `require_role` decorator in `hotel_app/dashboard_views.py` to render custom permission denied page
- Updated `require_permission` decorator to render custom permission denied page
- Both decorators now show the friendly error page instead of raising exceptions

**Files Modified:**
- `hotel_app/dashboard_views.py` - Updated `require_role` and `require_permission` decorators

### 2. Feedback Section Not Visible in Sidebar

**Problem:** User has `feedback.view` permission but Feedback section doesn't appear in sidebar.

**Root Cause:**
- `feedback_inbox` view was using `@user_passes_test(is_staff)` instead of `@require_section_permission('feedback', 'view')`
- Sidebar permission check might not be working correctly

**Fix Applied:**
- Updated `feedback_inbox` to use `@require_section_permission('feedback', 'view')`
- Updated `feedback_detail` to use `@require_section_permission('feedback', 'view')`
- Improved permission checking logic to be more reliable

**Files Modified:**
- `hotel_app/dashboard_views.py` - Updated feedback views to use section permissions
- `hotel_app/section_permissions.py` - Improved permission checking logic

### 3. Permission Check Reliability

**Problem:** Permission checks might not be working correctly due to Django's permission caching.

**Fix Applied:**
- Improved `user_has_section_permission` function to check groups directly
- Added better error handling and logging
- Added fallback checks for permission verification

**Files Modified:**
- `hotel_app/section_permissions.py` - Improved permission checking logic

## Testing Steps

### Step 1: Restart Django Server
**IMPORTANT:** You must restart the Django development server for the changes to take effect.

```bash
# Stop the server (Ctrl+C)
# Then restart it
python manage.py runserver
```

### Step 2: Verify Permissions in Database

```bash
# Check user permissions
python manage.py verify_user_permissions <username>

# Example:
python manage.py verify_user_permissions testuser
```

### Step 3: Assign Permissions to User's Group

1. **Login as superuser**
2. **Go to Manage Users → User Profiles**
3. **Click Edit on the user's group** (e.g., "Users" group)
4. **Check the permissions:**
   - ✓ Feedback - View
   - ✓ Users - View (if you want them to access profiles page)
5. **Click Save Permissions**
6. **Verify the permissions are saved**

### Step 4: Verify User is in Correct Group

1. **Go to Manage Users → All Users**
2. **Click on the test user**
3. **Verify the user is assigned to the correct group**
4. **Save if needed**

### Step 5: Test Sidebar Visibility

1. **Logout from test user account**
2. **Clear browser cache** (Ctrl+Shift+Delete or Ctrl+F5)
3. **Login as test user**
4. **Check sidebar:**
   - Feedback section should be visible if `feedback.view` is granted
   - Users section should be visible if `users.view` is granted
   - Sections without `view` permission should be hidden

### Step 6: Test Page Access

1. **Try accessing `/dashboard/feedback/`**
   - If permission granted: Page should load
   - If permission denied: Should see custom permission denied page

2. **Try accessing `/dashboard/manage-users/profiles/`**
   - If `users.view` granted: Page should load
   - If permission denied: Should see custom permission denied page (NOT 403 error)

### Step 7: Fix Permissions Programmatically (if needed)

```bash
# Fix permissions for a user
python manage.py fix_permissions <username> <section> <action> --group <group_name>

# Example: Give feedback.view permission to user in "Users" group
python manage.py fix_permissions testuser feedback view --group Users
```

## Debugging Commands

### Check User Permissions
```bash
python manage.py verify_user_permissions <username>
```

### Test Permission Check
```python
# Run in Django shell: python manage.py shell
from django.contrib.auth.models import User
from hotel_app.section_permissions import user_has_section_permission

user = User.objects.get(username='testuser')
print(f"Has feedback.view: {user_has_section_permission(user, 'feedback', 'view')}")
print(f"Has users.view: {user_has_section_permission(user, 'users', 'view')}")
```

### Check Group Permissions
```python
# Run in Django shell
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section

group = Group.objects.get(name='Users')
section = Section.objects.get(name='feedback')
section_ct = ContentType.objects.get_for_model(Section)
permission = Permission.objects.get(codename='view_feedback', content_type=section_ct)

print(f"Group has permission: {group.permissions.filter(id=permission.id).exists()}")
```

## Common Issues and Solutions

### Issue: Permission Not Showing After Assignment
**Solution:**
1. Restart Django server
2. Logout and login again
3. Clear browser cache
4. Verify permission is saved in database
5. Check that user is in correct group

### Issue: Sidebar Not Updating
**Solution:**
1. Sidebar is rendered server-side, so changes should reflect immediately
2. If not, clear browser cache
3. Verify template tag is working: `{% if user|has_section_permission:'feedback.view' %}`

### Issue: Still Getting 403 Error
**Solution:**
1. **Restart Django server** (most important!)
2. Verify decorators are updated
3. Check that `permission_denied.html` template exists
4. Clear browser cache
5. Check Django logs for errors

### Issue: Permission Check Returns False
**Solution:**
1. Verify permission exists in database
2. Verify user is in correct group
3. Verify group has the permission
4. Check permission codename format (should be `view_feedback`, not `feedback.view`)
5. Run: `python manage.py verify_user_permissions <username>`

## Verification Checklist

- [ ] Django server restarted
- [ ] User assigned to correct group
- [ ] Group has correct permissions
- [ ] Permissions saved in database
- [ ] User logged out and logged back in
- [ ] Browser cache cleared
- [ ] Sidebar shows correct sections
- [ ] Page access works correctly
- [ ] Permission denied page shows correctly (not 403 error)
- [ ] No errors in Django logs

## Files Changed

1. `hotel_app/dashboard_views.py`
   - Updated `require_role` decorator
   - Updated `require_permission` decorator
   - Updated `feedback_inbox` view
   - Updated `feedback_detail` view

2. `hotel_app/section_permissions.py`
   - Improved `user_has_section_permission` function
   - Added better error handling
   - Improved permission checking logic

3. `templates/dashboard/permission_denied.html`
   - Custom permission denied page (already created)

4. `hotel_app/management/commands/verify_user_permissions.py`
   - Command to verify user permissions

5. `hotel_app/management/commands/fix_permissions.py`
   - Command to fix permissions

## Next Steps

1. **Restart Django server** (required!)
2. **Test with a test user**
3. **Verify permissions are working**
4. **Check sidebar visibility**
5. **Test page access**
6. **Verify permission denied page shows correctly**

## Important Notes

- **Server Restart Required:** You must restart the Django server for decorator changes to take effect
- **Cache Clearing:** Users may need to logout/login and clear browser cache
- **Permission Format:** Permissions are stored as `view_feedback`, `add_feedback`, etc.
- **Group Assignment:** Users get permissions through groups, not directly
- **Superuser Bypass:** Superusers have all permissions automatically

