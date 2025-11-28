"""
Management command to fix/reset admin and test user passwords.
This ensures all users have correct passwords and group memberships.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hotel_app.models import UserProfile, Department


class Command(BaseCommand):
    help = 'Fix/reset admin and test user passwords and group memberships'

    def handle(self, *args, **options):
        self.stdout.write('Fixing user passwords and group memberships...\n')
        
        # Ensure groups exist
        admin_group, _ = Group.objects.get_or_create(name='Admins')
        staff_group, _ = Group.objects.get_or_create(name='Staff')
        users_group, _ = Group.objects.get_or_create(name='Users')
        
        # FIX ADMIN USER
        self.stdout.write('Fixing admin user...')
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@example.com',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('  Created admin user'))
        
        # Set password
        admin_user.set_password('admin')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        
        # Add to Admins group
        admin_user.groups.clear()
        admin_user.groups.add(admin_group)
        
        # Ensure profile exists
        dept = Department.objects.first()
        profile, _ = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'full_name': 'Administrator',
                'phone': '+1234567890',
                'title': 'System Administrator',
                'department': dept,
                'role': 'admin'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('  ✅ Admin user fixed (username: admin, password: admin)'))
        
        # FIX TEST_ADMIN USER
        self.stdout.write('Fixing test_admin user...')
        try:
            test_admin = User.objects.get(username='test_admin')
        except User.DoesNotExist:
            test_admin = User.objects.create_user(
                username='test_admin',
                email='admin@test.com',
                is_staff=True,
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS('  Created test_admin user'))
        
        test_admin.set_password('testpassword123')
        test_admin.is_staff = True
        test_admin.save()
        
        test_admin.groups.clear()
        test_admin.groups.add(admin_group)
        
        UserProfile.objects.get_or_create(
            user=test_admin,
            defaults={
                'full_name': 'Test Admin',
                'phone': '+1234567890',
                'title': 'Test Administrator',
                'department': dept,
                'role': 'admin'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('  ✅ Test admin fixed (username: test_admin, password: testpassword123)'))
        
        # FIX TEST_STAFF USER
        self.stdout.write('Fixing test_staff user...')
        try:
            test_staff = User.objects.get(username='test_staff')
        except User.DoesNotExist:
            test_staff = User.objects.create_user(
                username='test_staff',
                email='staff@test.com',
                is_staff=False,
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS('  Created test_staff user'))
        
        test_staff.set_password('testpassword123')
        test_staff.save()
        
        test_staff.groups.clear()
        test_staff.groups.add(staff_group)
        
        UserProfile.objects.get_or_create(
            user=test_staff,
            defaults={
                'full_name': 'Test Staff',
                'phone': '+1234567891',
                'title': 'Staff Member',
                'department': dept,
                'role': 'staff'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('  ✅ Test staff fixed (username: test_staff, password: testpassword123)'))
        
        # FIX TEST_USER USER
        self.stdout.write('Fixing test_user...')
        try:
            test_user = User.objects.get(username='test_user')
        except User.DoesNotExist:
            test_user = User.objects.create_user(
                username='test_user',
                email='user@test.com',
                is_staff=False,
                is_superuser=False
            )
            self.stdout.write(self.style.SUCCESS('  Created test_user'))
        
        test_user.set_password('testpassword123')
        test_user.save()
        
        test_user.groups.clear()
        test_user.groups.add(users_group)
        
        UserProfile.objects.get_or_create(
            user=test_user,
            defaults={
                'full_name': 'Test User',
                'phone': '+1234567892',
                'title': 'Regular User',
                'department': None,
                'role': 'user'
            }
        )
        
        self.stdout.write(self.style.SUCCESS('  ✅ Test user fixed (username: test_user, password: testpassword123)'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ All users have been fixed!'))
        self.stdout.write('='*60 + '\n')
        self.stdout.write(self.style.SUCCESS('You can now login with:'))
        self.stdout.write('  admin       / admin           (Superuser + Admins group)')
        self.stdout.write('  test_admin  / testpassword123 (Admins group)')
        self.stdout.write('  test_staff  / testpassword123 (Staff group)')
        self.stdout.write('  test_user   / testpassword123 (Users group)')
