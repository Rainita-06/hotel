"""
Management command to initialize sections and assign permissions to groups.
Creates Admins, Staff, and Users groups with appropriate permissions.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import Section


class Command(BaseCommand):
    help = 'Initialize sections and assign permissions to Admins, Staff, and Users groups'

    def handle(self, *args, **options):
        self.stdout.write('Initializing sections...')
        
        # Create/update all sections
        sections = Section.get_or_create_sections()
        self.stdout.write(self.style.SUCCESS(f'Created/updated {len(sections)} sections'))
        
        # Get or create groups
        admins_group, created = Group.objects.get_or_create(name='Admins')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Admins group'))
        
        staff_group, created = Group.objects.get_or_create(name='Staff')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Staff group'))
        
        users_group, created = Group.objects.get_or_create(name='Users')
        if created:
            self.stdout.write(self.style.SUCCESS('Created Users group'))
        
        # Get content type for Section model
        section_content_type = ContentType.objects.get_for_model(Section)
        
        # Clear existing permissions for all groups to start fresh
        admins_group.permissions.clear()
        staff_group.permissions.clear()
        users_group.permissions.clear()
        
        self.stdout.write('Assigning permissions to groups...')
        
        # Track permissions added
        admins_perms = 0
        staff_perms = 0
        users_perms = 0
        
        for section in sections:
            for action in ['view', 'add', 'change', 'delete']:
                codename = section.get_permission_codename(action)
                
                # Get or create permission
                permission, perm_created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=section_content_type,
                    defaults={
                        'name': f'Can {action} {section.display_name}',
                    }
                )
                
                if perm_created:
                    self.stdout.write(f'  Created permission: {codename}')
                
                # ADMINS: Get ALL permissions for ALL sections
                admins_group.permissions.add(permission)
                admins_perms += 1
                
                # STAFF: Get VIEW permission for all sections EXCEPT 'users'
                # No add/change/delete for staff
                if section.name != 'users' and action == 'view':
                    staff_group.permissions.add(permission)
                    staff_perms += 1
                
                # USERS: Only get VIEW permission for 'my_tickets' section
                # No dashboard, no other sections
                if section.name == 'my_tickets' and action == 'view':
                    users_group.permissions.add(permission)
                    users_perms += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Admins group: {admins_perms} permissions (full access)'))
        self.stdout.write(self.style.SUCCESS(f'✅ Staff group: {staff_perms} permissions (view all except users)'))
        self.stdout.write(self.style.SUCCESS(f'✅ Users group: {users_perms} permissions (only my tickets)'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Section initialization complete!'))
        self.stdout.write(self.style.WARNING(
            '\nPermission Summary:\n'
            '  - Admins: Full access to everything\n'
            '  - Staff: View access to all sections except Users\n'
            '  - Users: Only access to My Tickets section'
        ))
