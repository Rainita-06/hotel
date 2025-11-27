"""
Management command to create section-based permissions for the application.

This command creates permissions for each sidebar section with CRUD operations:
- {section}.view_section
- {section}.add_section
- {section}.change_section
- {section}.delete_section

These can be checked in templates as:
- {% if perms.hotel_app.view_users %}
- {% if perms.hotel_app.add_users %}
etc.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from hotel_app.models import Section


# Permission types for CRUD operations
PERMISSION_TYPES = [
    ('view', 'view'),
    ('add', 'add'),
    ('change', 'change'),
    ('delete', 'delete'),
]


class Command(BaseCommand):
    help = 'Create section-based permissions for all sidebar sections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating permissions',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        created_count = 0
        skipped_count = 0
        
        self.stdout.write(self.style.SUCCESS('Creating sections and permissions...'))
        
        try:
            # Get or create all sections
            sections = Section.get_or_create_sections()
            self.stdout.write(self.style.SUCCESS(f'Found/created {len(sections)} sections'))
            
            # Get ContentType for Section model
            section_content_type = ContentType.objects.get_for_model(Section)
            
            with transaction.atomic():
                for section in sections:
                    for perm_codename, perm_name in PERMISSION_TYPES:
                        codename = section.get_permission_codename(perm_codename)
                        name = f'Can {perm_name} {section.display_name}'
                        
                        # Check if permission already exists
                        permission, created = Permission.objects.get_or_create(
                            codename=codename,
                            content_type=section_content_type,
                            defaults={'name': name}
                        )
                        
                        if created:
                            created_count += 1
                            if not dry_run:
                                self.stdout.write(
                                    self.style.SUCCESS(f'  Created: {section.name}.{perm_codename}')
                                )
                            else:
                                self.stdout.write(
                                    self.style.WARNING(f'  Would create: {section.name}.{perm_codename}')
                                )
                        else:
                            skipped_count += 1
                            if not dry_run:
                                self.stdout.write(
                                    self.style.WARNING(f'  Already exists: {section.name}.{perm_codename}')
                                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating permissions: {str(e)}')
            )
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            return
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDry run complete. Would create {created_count} permissions, '
                    f'{skipped_count} already exist.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully created {created_count} permissions. '
                    f'{skipped_count} already existed.'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    '\nPermissions can be checked in templates as:'
                    '\n  {% if perms.hotel_app.view_users %}'
                    '\n  {% if perms.hotel_app.add_users %}'
                    '\n  {% if perms.hotel_app.change_users %}'
                    '\n  {% if perms.hotel_app.delete_users %}'
                )
            )
