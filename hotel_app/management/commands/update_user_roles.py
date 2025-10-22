from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hotel_app.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Update user profiles with roles based on their group memberships'

    def handle(self, *args, **options):
        # Get all users
        users = User.objects.all()
        
        for user in users:
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Set role based on group membership or superuser status
            if user.is_superuser:
                profile.role = 'admin'
            elif user.groups.filter(name='Admins').exists():
                profile.role = 'admin'
            elif user.groups.filter(name='Staff').exists():
                profile.role = 'staff'
            else:
                profile.role = 'user'
                
            profile.save()
            
            if created:
                self.stdout.write(f'Created profile for {user.username} with role {profile.role}')
            else:
                self.stdout.write(f'Updated profile for {user.username} with role {profile.role}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated roles for {users.count()} users')
        )