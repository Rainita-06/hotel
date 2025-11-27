"""
Management command to test section permissions.

Usage:
    python manage.py test_permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section
from hotel_app.section_permissions import user_has_section_permission


class Command(BaseCommand):
    help = 'Test section permissions system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Section Permissions System...\n'))
        
        # Check if sections exist
        sections = Section.objects.filter(is_active=True)
        if not sections.exists():
            self.stdout.write(self.style.WARNING('No sections found. Run: python manage.py create_section_permissions'))
            return
        
        self.stdout.write(f'Found {sections.count()} active sections:')
        for section in sections:
            self.stdout.write(f'  - {section.name} ({section.display_name})')
        
        # Check permissions
        section_content_type = ContentType.objects.get_for_model(Section)
        permissions = Permission.objects.filter(content_type=section_content_type)
        self.stdout.write(f'\nFound {permissions.count()} section permissions')
        
        # Check groups
        groups = Group.objects.all()
        self.stdout.write(f'\nFound {groups.count()} groups:')
        for group in groups:
            section_perms = group.permissions.filter(content_type=section_content_type)
            self.stdout.write(f'  - {group.name}: {section_perms.count()} section permissions')
            if section_perms.count() > 0:
                for perm in section_perms[:5]:  # Show first 5
                    self.stdout.write(f'    * {perm.codename}')
                if section_perms.count() > 5:
                    self.stdout.write(f'    ... and {section_perms.count() - 5} more')
        
        # Check users
        users = User.objects.all()
        self.stdout.write(f'\nFound {users.count()} users:')
        for user in users[:10]:  # Show first 10
            user_groups = user.groups.all()
            if user_groups.exists():
                group_names = ', '.join([g.name for g in user_groups])
                self.stdout.write(f'  - {user.username}: {group_names}')
            else:
                self.stdout.write(f'  - {user.username}: (no groups)')
        
        # Test permission checking
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Testing Permission Checks:')
        self.stdout.write('='*60)
        
        test_user = User.objects.filter(is_superuser=False).first()
        if test_user:
            self.stdout.write(f'\nTesting with user: {test_user.username}')
            test_sections = ['users', 'locations', 'tickets']
            for section_name in test_sections:
                for action in ['view', 'add', 'change', 'delete']:
                    has_perm = user_has_section_permission(test_user, section_name, action)
                    status = '✓' if has_perm else '✗'
                    self.stdout.write(f'  {status} {section_name}.{action}: {has_perm}')
        else:
            self.stdout.write(self.style.WARNING('No non-superuser found to test with'))
        
        # Superuser test
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            self.stdout.write(f'\nTesting with superuser: {superuser.username}')
            test_sections = ['users', 'locations', 'tickets']
            for section_name in test_sections:
                for action in ['view', 'add', 'change', 'delete']:
                    has_perm = user_has_section_permission(superuser, section_name, action)
                    status = '✓' if has_perm else '✗'
                    self.stdout.write(f'  {status} {section_name}.{action}: {has_perm}')
            if all(user_has_section_permission(superuser, 'users', 'view') for _ in range(1)):
                self.stdout.write(self.style.SUCCESS('  ✓ Superuser has all permissions (as expected)'))
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Permission test completed!'))
        self.stdout.write('='*60)

