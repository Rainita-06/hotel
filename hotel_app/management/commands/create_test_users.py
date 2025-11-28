"""
Management command to create test users with different roles for testing the RBAC system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hotel_app.models import UserProfile, Department


class Command(BaseCommand):
    help = 'Create test users with different roles for testing the RBAC system'

    def handle(self, *args, **options):
        self.stdout.write(
            'Creating/updating test users with different roles...'
        )

        # Get departments
        housekeeping_dept = Department.objects.filter(name='Housekeeping').first()
        front_desk_dept = Department.objects.filter(name='Front Desk').first()
        default_dept = Department.objects.first()  # Fallback to first department

        # Ensure groups exist
        try:
            admins_group = Group.objects.get(name='Admins')
            staff_group = Group.objects.get(name='Staff')
            users_group = Group.objects.get(name='Users')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'Groups not found! Please run: python manage.py init_sections'
            ))
            return

        # Create/Update Admin user
        admin_user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'admin@test.com',
                'is_staff': True,
                'is_superuser': False
            }
        )
        
        # Always set password (even if user existed)
        admin_user.set_password('testpassword123')
        admin_user.is_staff = True
        admin_user.is_superuser = False
        admin_user.save()
        
        # Clear and set groups
        admin_user.groups.clear()
        admin_user.groups.add(admins_group)
        
        # Create or update profile
        UserProfile.objects.update_or_create(
            user=admin_user,
            defaults={
                'full_name': 'Test Admin',
                'phone': '+1234567890',
                'title': 'System Administrator',
                'department': housekeeping_dept or default_dept,
                'role': 'admin'
            }
        )
        
        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'✅ {action} admin user: {admin_user.username} / testpassword123')
        )

        # Create/Update Staff user
        staff_user, created = User.objects.get_or_create(
            username='test_staff',
            defaults={
                'email': 'staff@test.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        
        # Always set password
        staff_user.set_password('testpassword123')
        staff_user.is_staff = False
        staff_user.save()
        
        # Clear and set groups
        staff_user.groups.clear()
        staff_user.groups.add(staff_group)
        
        # Create or update profile
        UserProfile.objects.update_or_create(
            user=staff_user,
            defaults={
                'full_name': 'Test Staff',
                'phone': '+1234567891',
                'title': 'Front Desk Agent',
                'department': front_desk_dept or default_dept,
                'role': 'staff'
            }
        )
        
        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'✅ {action} staff user: {staff_user.username} / testpassword123')
        )

        # Create/Update Regular user
        regular_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'user@test.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        
        # Always set password
        regular_user.set_password('testpassword123')
        regular_user.is_staff = False
        regular_user.save()
        
        # Clear and set groups
        regular_user.groups.clear()
        regular_user.groups.add(users_group)
        
        # Create or update profile
        UserProfile.objects.update_or_create(
            user=regular_user,
            defaults={
                'full_name': 'Test User',
                'phone': '+1234567892',
                'title': 'Guest',
                'department': None,
                'role': 'user'
            }
        )
        
        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'✅ {action} regular user: {regular_user.username} / testpassword123')
        )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS('✅ Test users creation/update completed successfully!')
        )
        self.stdout.write('='*60)
        self.stdout.write(
            '\nTest credentials:\n'
            '  test_admin  / testpassword123 (Admins group)\n'
            '  test_staff  / testpassword123 (Staff group)\n'
            '  test_user   / testpassword123 (Users group)'
        )