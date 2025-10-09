import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hotel_app.models import Department, ServiceRequest, RequestType, Location

class Command(BaseCommand):
    help = 'Create sample tickets for testing the My Tickets page'

    def handle(self, *args, **options):
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testuser', 
            defaults={
                'email': 'test@example.com', 
                'first_name': 'Test', 
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')

        # Get or create a department
        dept, created = Department.objects.get_or_create(
            name='Housekeeping', 
            defaults={'description': 'Housekeeping Department'}
        )
        if created:
            self.stdout.write(f'Created department: {dept.name}')

        # Update user profile with department
        if hasattr(user, 'userprofile'):
            user.userprofile.department = dept
            user.userprofile.save()
            self.stdout.write(f'Updated user profile with department: {dept.name}')

        # Create sample request type
        req_type, created = RequestType.objects.get_or_create(
            name='Room Cleaning', 
            defaults={'description': 'Clean the room'}
        )
        if created:
            self.stdout.write(f'Created request type: {req_type.name}')

        # Create sample location
        location, created = Location.objects.get_or_create(
            name='Room 101', 
            defaults={'room_no': '101'}
        )
        if created:
            self.stdout.write(f'Created location: {location.name}')

        # Create sample service requests
        for i in range(3):
            status = random.choice(['pending', 'assigned', 'in_progress'])
            sr = ServiceRequest.objects.create(
                request_type=req_type,
                location=location,
                requester_user=user,
                department=dept,
                priority='normal',
                status=status,
                notes=f'Sample ticket {i+1} for testing My Tickets page'
            )
            self.stdout.write(f'Created service request #{sr.id} with status: {status}')

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created sample data for testing! '
                'Login with username "testuser" and password "testpass123"'
            )
        )