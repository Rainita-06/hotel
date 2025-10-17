from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
import random

from hotel_app.models import GymMember


class Command(BaseCommand):
    help = 'Seed demo gym member data'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recreate demo gym members even if they exist')
        parser.add_argument('--count', type=int, default=10, help='Number of gym members to create (default: 10)')

    def handle(self, *args, **options):
        force = options['force']
        count = options['count']
        
        # Sample data for gym members
        first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma', 'Christopher', 'Olivia', 'Matthew', 'Sophia']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
        domains = ['example.com', 'test.com', 'demo.com', 'sample.com']
        
        created_count = 0
        
        for i in range(count):
            # Generate random data for each member
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{first_name} {last_name}"
            
            # Check if member already exists
            if not force and GymMember.objects.filter(full_name=full_name).exists():
                continue
                
            # Generate other data
            email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"
            phone = f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            address = f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm Dr', 'Cedar Ln'])}"
            city = random.choice(cities)
            
            # Generate dates
            start_date = timezone.now().date() - datetime.timedelta(days=random.randint(0, 365))
            end_date = start_date + datetime.timedelta(days=random.randint(30, 365))
            
            # Create gym member
            gym_member = GymMember(
                full_name=full_name,
                phone=phone,
                email=email,
                address=address,
                city=city,
                start_date=start_date,
                end_date=end_date,
                status=random.choice(['Active', 'Inactive', 'Suspended']),
                plan_type=random.choice(['Basic', 'Premium', 'VIP'])
            )
            
            gym_member.save()
            created_count += 1
            
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created/updated {created_count} gym members. '
                f'Use --force to recreate existing members.'
            )
        )