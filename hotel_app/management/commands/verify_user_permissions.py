"""
Management command to verify user permissions.

Usage:
    python manage.py verify_user_permissions <username>
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section
from hotel_app.section_permissions import user_has_section_permission


class Command(BaseCommand):
    help = 'Verify user permissions for section-based access'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to check permissions for')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\nChecking permissions for user: {user.username}'))
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Is Superuser: {user.is_superuser}')
        self.stdout.write(f'Is Staff: {user.is_staff}')
        self.stdout.write(f'Is Active: {user.is_active}')
        
        # Show groups
        groups = user.groups.all()
        self.stdout.write(f'\nGroups ({groups.count()}):')
        for group in groups:
            self.stdout.write(f'  - {group.name}')
        
        # Show section permissions
        section_content_type = ContentType.objects.get_for_model(Section)
        sections = Section.objects.filter(is_active=True).order_by('name')
        
        self.stdout.write(f'\nSection Permissions:')
        self.stdout.write('=' * 60)
        
        for section in sections:
            self.stdout.write(f'\n{section.display_name} ({section.name}):')
            for action in ['view', 'add', 'change', 'delete']:
                has_perm = user_has_section_permission(user, section.name, action)
                status = '✓' if has_perm else '✗'
                self.stdout.write(f'  {status} {action}: {has_perm}')
                
                # Show which groups have this permission
                if has_perm:
                    perm_codename = section.get_permission_codename(action)
                    try:
                        permission = Permission.objects.get(
                            codename=perm_codename,
                            content_type=section_content_type
                        )
                        groups_with_perm = Group.objects.filter(permissions=permission)
                        user_groups_with_perm = groups_with_perm.filter(id__in=user.groups.all())
                        if user_groups_with_perm.exists():
                            group_names = ', '.join([g.name for g in user_groups_with_perm])
                            self.stdout.write(f'    (from groups: {group_names})')
                    except Permission.DoesNotExist:
                        pass
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Permission check completed!'))

