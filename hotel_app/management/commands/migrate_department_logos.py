import os
from django.core.management.base import BaseCommand
from django.conf import settings
from hotel_app.models import Department

class Command(BaseCommand):
    help = 'Migrate existing department logos to the new directory structure'

    def handle(self, *args, **options):
        departments = Department.objects.exclude(logo=None)
        
        for dept in departments:
            if dept.logo and dept.pk:
                # Check if the logo is already in the new structure
                if f'departments/{dept.pk}/' in dept.logo.name:
                    self.stdout.write(f"Department {dept.name} logo already in new structure")
                    continue
                
                # Create department directory if it doesn't exist
                dept_dir = os.path.join(settings.MEDIA_ROOT, 'departments', str(dept.pk))
                os.makedirs(dept_dir, exist_ok=True)
                
                # Get the current logo file path
                old_path = dept.logo.path
                
                # Define new file path
                filename = os.path.basename(old_path)
                new_path = os.path.join(dept_dir, filename)
                
                # Move the file
                try:
                    # Copy the file to the new location
                    with open(old_path, 'rb') as old_file:
                        with open(new_path, 'wb') as new_file:
                            new_file.write(old_file.read())
                    
                    # Update the department's logo field
                    media_url = settings.MEDIA_URL or '/media/'
                    if not media_url.endswith('/'):
                        media_url = media_url + '/'
                    dept.logo = f"{media_url}departments/{dept.pk}/{filename}"
                    dept.save(update_fields=['logo'])
                    
                    self.stdout.write(f"Successfully migrated logo for department {dept.name}")
                except Exception as e:
                    self.stdout.write(f"Failed to migrate logo for department {dept.name}: {str(e)}")
        
        self.stdout.write(self.style.SUCCESS('Successfully migrated all department logos'))