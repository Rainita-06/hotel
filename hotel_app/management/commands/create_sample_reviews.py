import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from hotel_app.models import Review, Guest

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample reviews for testing pagination'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=25, help='Number of reviews to create')

    def handle(self, *args, **options):
        count = options['count']
        
        # Create some sample guests if none exist
        if not Guest.objects.exists():
            for i in range(10):
                Guest.objects.create(
                    full_name=f'Guest {i+1}',
                    room_number=f'{100 + i}',
                    email=f'guest{i+1}@example.com'
                )
        
        guests = list(Guest.objects.all())
        
        # Sample comments for variety
        sample_comments = [
            "Excellent service and comfortable room. Will definitely stay again!",
            "The staff was very helpful and the amenities were great.",
            "Average experience. Room was clean but could use some upgrades.",
            "Disappointing stay. The room was not as advertised and service was slow.",
            "Outstanding experience! The hotel exceeded all my expectations.",
            "Good value for money. Convenient location and friendly staff.",
            "The room was noisy and the air conditioning didn't work properly.",
            "Pleasant surprise. The hotel was much better than I expected.",
            "Mediocre experience. Nothing特别 memorable about the stay.",
            "Fantastic location and great breakfast options. Highly recommend!"
        ]
        
        # Create reviews
        for i in range(count):
            guest = random.choice(guests)
            rating = random.randint(1, 5)
            comment = random.choice(sample_comments)
            
            Review.objects.create(
                guest=guest,
                rating=rating,
                comment=comment
            )
            
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} sample reviews')
        )