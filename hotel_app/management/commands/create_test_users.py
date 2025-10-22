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
            'Creating test users with different roles...'
        )

        # Create departments if they don't exist
        housekeeping_dept, _ = Department.objects.get_or_create(
            name='Housekeeping',
            defaults={'description': 'Housekeeping department'}
        )
        
        front_desk_dept, _ = Department.objects.get_or_create(
            name='Front Desk',
            defaults={'description': 'Front Desk department'}
        )

        # Create Admin user
        try:
            admin_user = User.objects.get(username='test_admin')
            self.stdout.write(f'Found existing admin user: {admin_user.username}')
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                username='test_admin',
                email='admin@test.com',
                password='testpassword123',
                is_staff=True,
                is_superuser=False
            )
            
            # Create user profile
            UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'full_name': 'Test Admin',
                    'phone': '+1234567890',
                    'title': 'System Administrator',
                    'department': housekeeping_dept,
                    'role': 'admin'
                }
            )
            
            # Assign to Admins group
            admins_group = Group.objects.get(name='Admins')
            admin_user.groups.add(admins_group)
            
            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: {admin_user.username}')
            )

        # Create Staff user
        try:
            staff_user = User.objects.get(username='test_staff')
            self.stdout.write(f'Found existing staff user: {staff_user.username}')
        except User.DoesNotExist:
            staff_user = User.objects.create_user(
                username='test_staff',
                email='staff@test.com',
                password='testpassword123',
                is_staff=False,
                is_superuser=False
            )
            
            # Create user profile
            UserProfile.objects.get_or_create(
                user=staff_user,
                defaults={
                    'full_name': 'Test Staff',
                    'phone': '+1234567891',
                    'title': 'Front Desk Agent',
                    'department': front_desk_dept,
                    'role': 'staff'
                }
            )
            
            # Assign to Staff group
            staff_group = Group.objects.get(name='Staff')
            staff_user.groups.add(staff_group)
            
            self.stdout.write(
                self.style.SUCCESS(f'Created staff user: {staff_user.username}')
            )

        # Create Regular user
        try:
            regular_user = User.objects.get(username='test_user')
            self.stdout.write(f'Found existing regular user: {regular_user.username}')
        except User.DoesNotExist:
            regular_user = User.objects.create_user(
                username='test_user',
                email='user@test.com',
                password='testpassword123',
                is_staff=False,
                is_superuser=False
            )
            
            # Create user profile
            UserProfile.objects.get_or_create(
                user=regular_user,
                defaults={
                    'full_name': 'Test User',
                    'phone': '+1234567892',
                    'title': 'Guest',
                    'department': None,
                    'role': 'user'
                }
            )
            
            # Assign to Users group
            users_group = Group.objects.get(name='Users')
            regular_user.groups.add(users_group)
            
            self.stdout.write(
                self.style.SUCCESS(f'Created regular user: {regular_user.username}')
            )

        self.stdout.write(
            self.style.SUCCESS('Test users creation completed successfully!')
        )
        self.stdout.write(
            'Test credentials:\n'
            'Admin: test_admin / testpassword123\n'
            'Staff: test_staff / testpassword123\n'
            'User: test_user / testpassword123'
        )