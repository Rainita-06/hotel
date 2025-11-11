"""
Management command to check feedback permission for a user.

Usage:
    python manage.py check_feedback_permission <username>
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section
from hotel_app.section_permissions import user_has_section_permission


class Command(BaseCommand):
    help = 'Check feedback permission for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to check')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n=== Checking Feedback Permission for {username} ===\n'))
        
        # Check if feedback section exists
        try:
            section = Section.objects.get(name='feedback', is_active=True)
            self.stdout.write(f'✓ Feedback section exists: {section.display_name}')
        except Section.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ Feedback section not found or not active'))
            return
        
        # Get permission
        section_content_type = ContentType.objects.get_for_model(Section)
        try:
            permission = Permission.objects.get(
                codename='view_feedback',
                content_type=section_content_type
            )
            self.stdout.write(f'✓ Permission exists: {permission.codename}')
        except Permission.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ Permission "view_feedback" not found'))
            self.stdout.write(self.style.WARNING('Run: python manage.py create_section_permissions'))
            return
        
        # Check user's groups
        user_groups = user.groups.all()
        self.stdout.write(f'\nUser groups ({user_groups.count()}):')
        for group in user_groups:
            self.stdout.write(f'  - {group.name}')
            
            # Check if group has the permission
            group_has_perm = group.permissions.filter(id=permission.id).exists()
            if group_has_perm:
                self.stdout.write(self.style.SUCCESS(f'    ✓ Group "{group.name}" has feedback.view permission'))
            else:
                self.stdout.write(f'    ✗ Group "{group.name}" does NOT have feedback.view permission')
        
        # Check which groups have this permission
        groups_with_perm = Group.objects.filter(permissions=permission)
        self.stdout.write(f'\nGroups with feedback.view permission ({groups_with_perm.count()}):')
        for group in groups_with_perm:
            self.stdout.write(f'  - {group.name}')
            if user.groups.filter(id=group.id).exists():
                self.stdout.write(self.style.SUCCESS(f'    ✓ User is in this group'))
            else:
                self.stdout.write(f'    ✗ User is NOT in this group')
        
        # Test permission check
        self.stdout.write(f'\n=== Permission Check Result ===')
        has_perm = user_has_section_permission(user, 'feedback', 'view')
        if has_perm:
            self.stdout.write(self.style.SUCCESS(f'✓ user_has_section_permission(user, "feedback", "view") = TRUE'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ user_has_section_permission(user, "feedback", "view") = FALSE'))
            self.stdout.write(self.style.WARNING('\nTroubleshooting:'))
            self.stdout.write('1. Verify user is in a group that has feedback.view permission')
            self.stdout.write('2. Verify the group has the permission assigned')
            self.stdout.write('3. Try logging out and logging back in')
            self.stdout.write('4. Check Django logs for permission errors')

