"""
Management command to debug permission issues for a specific user.

Usage:
    python manage.py debug_permissions <username>
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section
from hotel_app.section_permissions import user_has_section_permission


class Command(BaseCommand):
    help = 'Debug permission issues for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to debug')
        parser.add_argument('--section', type=str, default='feedback', help='Section name to check (default: feedback)')

    def handle(self, *args, **options):
        username = options['username']
        section_name = options['section']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Debugging Permissions for {username} ===\n'))
        
        # Check if section exists
        try:
            section = Section.objects.get(name=section_name, is_active=True)
            self.stdout.write(f'✓ Section exists: {section.display_name} ({section.name})')
        except Section.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ Section "{section_name}" not found or not active'))
            return
        
        # Get permission
        section_content_type = ContentType.objects.get_for_model(Section)
        codename = section.get_permission_codename('view')
        
        try:
            permission = Permission.objects.get(
                codename=codename,
                content_type=section_content_type
            )
            self.stdout.write(f'✓ Permission exists: {permission.codename} (ID: {permission.id})')
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ Permission "{codename}" not found'))
            self.stdout.write(self.style.WARNING('Run: python manage.py create_section_permissions'))
            return
        
        # Check user's groups
        user_groups = user.groups.all()
        self.stdout.write(f'\nUser groups ({user_groups.count()}):')
        has_permission = False
        for group in user_groups:
            self.stdout.write(f'  - {group.name} (ID: {group.id})')
            
            # Check if group has the permission
            group_permissions = group.permissions.all()
            group_has_perm = group_permissions.filter(id=permission.id).exists()
            
            if group_has_perm:
                self.stdout.write(self.style.SUCCESS(f'    ✓ Group "{group.name}" has {codename} permission'))
                has_permission = True
            else:
                self.stdout.write(f'    ✗ Group "{group.name}" does NOT have {codename} permission')
                self.stdout.write(f'      Group has {group_permissions.count()} permissions')
        
        # Test permission check function
        self.stdout.write(f'\n=== Permission Check Results ===')
        result = user_has_section_permission(user, section_name, 'view')
        if result:
            self.stdout.write(self.style.SUCCESS(f'✓ user_has_section_permission(user, "{section_name}", "view") = TRUE'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ user_has_section_permission(user, "{section_name}", "view") = FALSE'))
        
        # Check Django's has_perm
        try:
            django_has_perm = user.has_perm(f'hotel_app.{codename}')
            if django_has_perm:
                self.stdout.write(self.style.SUCCESS(f'✓ user.has_perm("hotel_app.{codename}") = TRUE'))
            else:
                self.stdout.write(f'✗ user.has_perm("hotel_app.{codename}") = FALSE')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠ user.has_perm() error: {str(e)}'))
        
        # Recommendations
        if not has_permission:
            self.stdout.write(self.style.WARNING('\n=== Recommendations ==='))
            self.stdout.write('1. Assign the user to a group that has the permission')
            self.stdout.write('2. Or assign the permission directly to the user')
            self.stdout.write('3. After making changes, the user should logout and login again')
            self.stdout.write('4. Clear browser cache')

