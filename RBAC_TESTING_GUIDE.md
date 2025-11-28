# User Profiles & RBAC Testing Guide

## System Overview

The hotel management system uses Django's built-in **Groups** and **Permissions** system combined with a custom **Section** model for Role-Based Access Control (RBAC).

### Architecture

1. **Django Groups**: Admins, Staff, Users
2. **Section Model**: Represents each sidebar section (Users, Locations, Tickets, etc.)
3. **Permissions**: Each section has 4 types: view, add, change, delete
4. **User Profiles**: Connected to Groups via Django's built-in Group membership

## Setup Complete

✅ Sections have been initialized
✅ Permissions have been created
✅ Admins group has ALL permissions by default
✅ Staff group has operational permissions
✅ Users group has limited permissions

## How to Test

### Step 1: Access Admin Account

1. Log in with your admin account (superuser or member of "Admins" group)
2. Navigate to: `/dashboard/manage-users/profiles/`
3. You should see:
   - Cards for Admins, Staff, and Users groups
   - Permission lists for each group
   - Module Permissions Overview table
   - Edit/Copy buttons (visible to admins)

### Step 2: Create a Test User with Limited Permissions

#### Option A: Using Django Admin

1. Go to: `/admin/auth/user/`
2. Click "Add User"
3. Create a test user (e.g., username: `teststaff`, password: `testpass123`)
4. After creation:
   - Go to "Groups" section
   - Add user to "Staff" or "Users" group
   - Save

#### Option B: Using the Dashboard

1. Go to: `/dashboard/manage-users/all/`
2. Create a new user
3. Assign them to a group (Staff or Users)

### Step 3: Modify Permissions for a Group

1. As admin, go to `/admin/auth/group/`
2. Click on "Staff" or "Users" group
3. In the "Permissions" section:
   - **Remove** some permissions (e.g., remove "Can view locations")
   - **Add** some permissions if needed
   - Click "Save"

### Step 4: Test with the Limited User

1. **Log out** from admin account
2. **Log in** with the test user you created
3. Check the sidebar:
   - ✅ Only sections the user has `view` permission for should appear
   - ❌ Sections without permission should be hidden

### Step 5: Test Permission Denied Page

1. While logged in as the limited user
2. Try to access a URL they don't have permission for
   - Example: If they don't have "Can view Users" permission
   - Manually navigate to: `/dashboard/manage-users/`
   
3. Expected behavior:
   - ✅ You should see a "Permission Denied" page
   - ✅ Page shows: "You don't have permission to access this page"
   - ✅ Shows which permission is required
   - ✅ Offers a button to go back to Dashboard or previous allowed section

## Permission Matrix

### Admins Group
- **All Sections**: Full access (view, add, change, delete)

### Staff Group (Default Permissions)
- **Dashboard**: View
- **Tickets**: View, Add, Change
- **Messaging**: View, Add, Change
- **Gym**: View, Add, Change
- **Locations**: View
- **Breakfast Voucher**: View, Add, Change
- **Feedback**: View, Add, Change

### Users Group (Default Permissions)
- **Dashboard**: View
- **My Tickets**: View

## Customizing Permissions

### Via Django Admin

1. Go to `/admin/auth/group/`
2. Select the group (e.g., "Staff")
3. Use the filter to find section permissions:
   - Filter by "content type" = "section"
4. Add/remove permissions as needed
5. Save changes

### Via Code (Management Command)

If you need to reset or customize permissions, edit:
`hotel_app/management/commands/init_sections.py`

Then run:
```bash
python manage.py init_sections
```

## Testing Checklist

- [ ] Admin user can see ALL sidebar sections
- [ ] Admin user can access ALL URLs
- [ ] Staff user sees only permitted sections in sidebar
- [ ] Staff user gets "Permission Denied" for unauthorized URLs
- [ ] User persona sees only basic sections (Dashboard, My Tickets)
- [ ] Permission Denied page shows correct message
- [ ] Permission Denied page offers redirect to allowed section
- [ ] Changes to group permissions reflect immediately after re-login
- [ ] User Profiles page shows correct permission matrix
- [ ] Permission API endpoints work (`/dashboard/api/groups/<id>/permissions/`)

## Troubleshooting

### Sidebar shows all sections even for limited users

**Solution**: 
1. Check if the user is a superuser (`is_superuser=True`)
2. Superusers bypass all permission checks
3. Use `/admin/auth/user/` to uncheck "Superuser status"

### Permission Denied page doesn't show

**Solution**:
1. Check that decorators are applied to views in `dashboard_views.py`
2. Look for `@require_section_permission('section_name', 'action')`
3. If missing, the view won't check permissions

### Permissions don't update after changing them

**Solution**:
1. Log out completely
2. Clear browser cache
3. Log back in
4. Django caches permissions per session

### User Profiles page shows "No user groups found"

**Solution**:
1. Run `python manage.py init_sections` to create groups
2. Check database: `select * from auth_group;`
3. Ensure Groups table has Admins, Staff, Users

## Database Schema

```
auth_user (Django's User table)
└── auth_user_groups (Many-to-Many)
    └── auth_group (Groups: Admins, Staff, Users)
        └── auth_group_permissions (Many-to-Many)
            └── auth_permission
                └── django_content_type (Points to Section model)
                    └── section (Custom table with sidebar sections)
```

## API Endpoints for Testing

- **Get group permissions**: GET `/dashboard/api/groups/<group_id>/permissions/`
- **Update group permissions**: POST `/dashboard/api/groups/<group_id>/permissions/update/`
- **Get group members**: GET `/dashboard/api/groups/<group_id>/members/`

## Important Files

- **Sidebar**: `templates/dashboard/components/sidebar.html`
- **Permission Denied**: `templates/dashboard/permission_denied.html`
- **User Profiles**: `templates/dashboard/user_profiles.html`
- **Section Permissions**: `hotel_app/section_permissions.py`
- **Template Tags**: `hotel_app/templatetags/section_permissions.py`
- **Management Command**: `hotel_app/management/commands/init_sections.py`
- **Views**: `hotel_app/dashboard_views.py`

## Expected Flow

```
User Login → Check Groups → Load Permissions → Filter Sidebar Sections
                              ↓
                     User tries to access URL
                              ↓
                View decorator checks permission
                              ↓
            Permission OK?  ←  YES → Show page
                ↓ NO
         Show Permission Denied Page
                ↓
         Redirect to Dashboard or Back
```

## Success Criteria

1. ✅ Admins see everything and can access everything
2. ✅ Staff see limited sections based on their permissions
3. ✅ Users see minimal sections (Dashboard, My Tickets)
4. ✅ Unauthorized access shows Permission Denied page
5. ✅ Permission changes reflect after re-login
6. ✅ User Profiles page displays correctly
7. ✅ API endpoints return correct permission data
