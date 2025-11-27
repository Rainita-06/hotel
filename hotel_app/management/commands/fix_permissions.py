"""
Management command to fix and verify permissions.

Usage:
    python manage.py fix_permissions <username> <section_name> <action>
    python manage.py fix_permissions testuser feedback view
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section
from hotel_app.section_permissions import user_has_section_permission


class Command(BaseCommand):
    help = 'Fix and verify user permissions'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('section_name', type=str, help='Section name (e.g., feedback, users)')
        parser.add_argument('action', type=str, help='Action (view, add, change, delete)')
        parser.add_argument('--group', type=str, help='Group name to assign permission to')

    def handle(self, *args, **options):
        username = options['username']
        section_name = options['section_name']
        action = options['action']
        group_name = options.get('group')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        try:
            section = Section.objects.get(name=section_name, is_active=True)
        except Section.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Section "{section_name}" not found'))
            return
        
        section_content_type = ContentType.objects.get_for_model(Section)
        codename = section.get_permission_codename(action)
        
        try:
            permission = Permission.objects.get(
                codename=codename,
                content_type=section_content_type
            )
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Permission "{codename}" not found. Run: python manage.py create_section_permissions'))
            return
        
        # Assign permission to group
        if group_name:
            try:
                group = Group.objects.get(name=group_name)
                group.permissions.add(permission)
                self.stdout.write(self.style.SUCCESS(f'Added permission {codename} to group {group_name}'))
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Group "{group_name}" not found'))
                return
        else:
            # Assign to user's first group
            user_groups = user.groups.all()
            if user_groups.exists():
                group = user_groups.first()
                group.permissions.add(permission)
                self.stdout.write(self.style.SUCCESS(f'Added permission {codename} to group {group.name}'))
            else:
                self.stdout.write(self.style.ERROR(f'User has no groups. Please assign user to a group first.'))
                return
        
        # Verify permission
        has_perm = user_has_section_permission(user, section_name, action)
        self.stdout.write(f'\nVerification:')
        self.stdout.write(f'  User: {user.username}')
        self.stdout.write(f'  Section: {section_name}')
        self.stdout.write(f'  Action: {action}')
        self.stdout.write(f'  Permission: {codename}')
        self.stdout.write(f'  Has permission: {has_perm}')
        
        if has_perm:
            self.stdout.write(self.style.SUCCESS('✓ Permission verified successfully!'))
        else:
            self.stdout.write(self.style.WARNING('✗ Permission check failed. User may need to logout and login again.'))

