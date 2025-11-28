# User Authentication Fix Guide - Docker Deployment

## Problem
- Only admin:admin credentials work on some systems
- admin:admin credentials  don't work on other systems
- Test users (test_admin, test_staff, test_user) can't login

## Root Cause
The issue occurs because:
1. Groups might not exist when users are created (wrong order)
2. Passwords might not be properly hashed
3. Admin user might not be added to Admins group

## Solution

### Option 1: Quick Fix (For Existing Deployments)

Run the fix script in PowerShell:

```powershell
.\fix_users.ps1
```

This will:
- Reset all user passwords
- Add users to correct groups
- Fix group memberships

### Option 2: Full Redeployment

1. Stop and remove existing containers:
```powershell
docker-compose -f docker-compose.prod.yml down -v
```

2. Run the updated deployment script:
```powershell
.\deploy_simple.ps1
```

The updated script now:
- Creates groups FIRST (via init_sections)
- Then creates departments
- Then creates admin and adds to Admins group
- Finally creates test users

### Option 3: Manual Fix (Advanced)

If you prefer to fix manually:

```powershell
# Access the Docker container
docker exec -it hotel_web bash

# Run Django shell
python manage.py shell

# In the shell, run:
from django.contrib.auth.models import User, Group
from hotel_app.models import UserProfile

# Fix admin user
admin = User.objects.get(username='admin')
admin.set_password('admin')
admin.is_superuser = True
admin.is_staff = True
admin.save()
admin_group = Group.objects.get(name='Admins')
admin.groups.clear()
admin.groups.add(admin_group)
print("Admin fixed!")

# Fix test_admin
test_admin = User.objects.get(username='test_admin')
test_admin.set_password('testpassword123')
test_admin.save()
test_admin.groups.clear()
test_admin.groups.add(admin_group)
print("Test admin fixed!")

# Fix test_staff  
test_staff = User.objects.get(username='test_staff')
test_staff.set_password('testpassword123')
test_staff.save()
staff_group = Group.objects.get(name='Staff')
test_staff.groups.clear()
test_staff.groups.add(staff_group)
print("Test staff fixed!")

# Fix test_user
test_user = User.objects.get(username='test_user')
test_user.set_password('testpassword123')
test_user.save()
users_group = Group.objects.get(name='Users')
test_user.groups.clear()
test_user.groups.add(users_group)
print("Test user fixed!")

# Exit shell
exit()
```

## Testing After Fix

### Test Admin User (admin:admin)
1. Go to http://localhost:8080
2. Login with:
   - Username: `admin`
   - Password: `admin`
3. You should see ALL sidebar sections
4. Check you're in the Admins group: Go to your profile or Django admin

### Test Admin User (test_admin:testpassword123)
1. Logout
2. Login with:
   - Username: `test_admin`
   - Password: `testpassword123`
3. Should see all sections (same as admin)

### Test Staff User (test_staff:testpassword123)
1. Logout
2. Login with:
   - Username: `test_staff`
   - Password: `testpassword123`
3. Should see all sections EXCEPT "Users"
4. Try accessing `/dashboard/manage-users/` → Should get "Permission Denied"

### Test Regular User (test_user:testpassword123)
1. Logout
2. Login with:
   - Username: `test_user`
   - Password: `testpassword123`
3. Should ONLY see "My Tickets" section
4. Should NOT see Dashboard (will redirect to My Tickets)

## Verification Checklist

- [ ] admin:admin works on your system
- [ ] admin:admin works on other systems
- [ ] test_admin:testpassword123 works
- [ ] test_staff:testpassword123 works
- [ ] test_user:testpassword123 works
- [ ] Each user sees correct sidebar sections based on their role
- [ ] Permission denied works for unauthorized access

## Common Issues

### Issue: "User does not exist"
**Solution**: Run `docker exec hotel_web python manage.py create_test_users`

### Issue: "Incorrect password"
**Solution**: Run `.\fix_users.ps1` or manually reset using Django shell

### Issue: "No groups found"
**Solution**: Run `docker exec hotel_web python manage.py init_sections`

### Issue: Users can't see any sections
**Solution**: 
1. Check if user is in a group: Django admin → Users → Select user → Check "Groups"
2. Run `.\fix_users.ps1` to reassign groups

### Issue: Changes don't persist after container restart
**Solution**: 
1. Make sure you're using volumes in docker-compose
2. Don't use `-v` flag when running `docker-compose down` (it deletes volumes)

## Files Modified

1. `deploy_simple.ps1` - Updated deployment order
2. `hotel_app/management/commands/fix_users.py` - New command to fix users
3. `fix_users.ps1` - Quick fix script for Docker
4. `hotel_app/management/commands/init_sections.py` - Creates groups first

## Deployment Order (Correct)

1. ✅ `init_sections` - Creates groups and permissions
2. ✅ `init_departments` - Creates departments
3. ✅ Create admin user and add to Admins group
4. ✅ `create_test_users` - Creates test users (groups already exist)

## Support

If issues persist:
1. Check Docker logs: `docker logs hotel_web`
2. Check database connection
3. Verify .env file has correct DB credentials
4. Try full redeployment with volume cleanup

## Quick Reference

| Username | Password | Group | Access Level |
|----------|----------|-------|--------------|
| admin | admin | Admins (+ Superuser) | Everything |
| test_admin | testpassword123 | Admins | Everything |
| test_staff | testpassword123 | Staff | View all except Users |
| test_user | testpassword123 | Users | Only My Tickets |
