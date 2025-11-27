from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
import random

from hotel_app.models import (
    Department, Building, Floor, LocationFamily, LocationType, Location,
    RequestFamily, WorkFamily, Workflow, RequestType, ServiceRequest,
    Guest, Booking, Voucher, Complaint, Review, GuestComment
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for dashboard charts (requests & feedback) and related models.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recreate demo objects even if they exist')
        parser.add_argument('--requests', action='store_true', help='Seed requests/service request demo data')
        parser.add_argument('--reviews', action='store_true', help='Seed guest reviews/feedback demo data')

    def handle(self, *args, **options):
        force = options['force']
        seed_requests = options['requests']
        seed_reviews = options['reviews']

        now = timezone.now()
        today = now.date()

        # Create demo department
        dept, created = Department.objects.get_or_create(name='Demo Department')
        if created or force:
            dept.description = 'Department created by seed_demo_data management command'
            dept.save()
        self.stdout.write(self.style.SUCCESS(f'Department: {dept.name}'))

        # Create a demo user
        demo_username = 'demo_user'
        demo_email = 'demo@example.com'
        demo_password = 'demo_pass_123'
        user, created = User.objects.get_or_create(username=demo_username, defaults={'email': demo_email})
        if created or force:
            user.set_password(demo_password)
            user.save()
        self.stdout.write(self.style.SUCCESS(f'User: {user.username}'))

        # Create location hierarchy
        building, _ = Building.objects.get_or_create(name='Demo Building')
        floor, _ = Floor.objects.get_or_create(building=building, floor_number=1)
        family, _ = LocationFamily.objects.get_or_create(name='Guest Room')
        ltype, _ = LocationType.objects.get_or_create(name='Standard Room', defaults={'family': family})
        location, _ = Location.objects.get_or_create(building=building, floor=floor, room_no='101', defaults={
            'family': family, 'type': ltype, 'name': 'Demo Room 101', 'capacity': 2
        })
        self.stdout.write(self.style.SUCCESS(f'Location: {location}'))

        # Create a demo guest and booking
        guest, created = Guest.objects.get_or_create(
            email='guest@example.com',
            defaults={
                'full_name': 'Demo Guest',
                'room_number': '101',
                'checkin_date': today - datetime.timedelta(days=1),
                'checkout_date': today + datetime.timedelta(days=2),
                'breakfast_included': True,
                'created_at': now,
            }
        )
        if created or force:
            guest.save()
        self.stdout.write(self.style.SUCCESS(f'Guest: {guest}'))

        booking, created = Booking.objects.get_or_create(
            guest=guest,
            room_number='101',
            defaults={
                'check_in': datetime.datetime.combine(today - datetime.timedelta(days=1), datetime.time(hour=14), tzinfo=timezone.get_current_timezone()),
                'check_out': datetime.datetime.combine(today + datetime.timedelta(days=2), datetime.time(hour=12), tzinfo=timezone.get_current_timezone()),
            }
        )
        if created or force:
            booking.save()
        self.stdout.write(self.style.SUCCESS(f'Booking: {booking.booking_reference}'))

        # Voucher
        voucher, created = Voucher.objects.get_or_create(
            booking=booking,
            defaults={
                'guest_name': guest.full_name,
                'room_no': booking.room_number,
                'check_in_date': guest.checkin_date,
                'check_out_date': guest.checkout_date,
                'valid_dates': [(today + datetime.timedelta(days=i)).isoformat() for i in range(0, 3)],
                'quantity': 1,
                'adults': 1,
                'kids': 0,
                'phone_number': '+1234567890',
                'country_code': '+1',
            }
        )
        if created or force:
            voucher.save()
        self.stdout.write(self.style.SUCCESS(f'Voucher: {voucher.voucher_code}'))

        # Complaints
        comp_subjects = [
            'WiFi not working', 'AC malfunction', 'No hot water in shower',
            'Room not cleaned', 'Late checkout issue'
        ]
        for i, sub in enumerate(comp_subjects[:3]):
            comp, created = Complaint.objects.get_or_create(
                subject=sub,
                defaults={
                    'description': f'Demo: {sub}',
                    'status': random.choice(['pending', 'in_progress', 'resolved']),
                    'guest': guest if i % 2 == 0 else None,
                }
            )
            if created or force:
                comp.save()
        self.stdout.write(self.style.SUCCESS('Complaints seeded'))

        # Reviews / Feedback
        if seed_reviews or not Review.objects.exists():
            ratings = [5, 4, 3, 2, 1, 5, 4]
            for i, r in enumerate(ratings):
                rev, created = Review.objects.get_or_create(guest=guest, rating=r, defaults={
                    'comment': f'Demo review {i+1}',
                    'created_at': now - datetime.timedelta(days=i)
                })
                if created or force:
                    rev.save()
            self.stdout.write(self.style.SUCCESS('Reviews seeded'))

        # Request types and service requests (requests chart)
        if seed_requests or not RequestType.objects.exists():
            types = ['Housekeeping', 'Maintenance', 'Room Service', 'Concierge']
            req_types = []
            for t in types:
                rt, _ = RequestType.objects.get_or_create(name=t)
                req_types.append(rt)

            # Create some service requests across types and status
            statuses = ['open', 'in_progress', 'closed']
            for i in range(12):
                rt = random.choice(req_types)
                sr, created = ServiceRequest.objects.get_or_create(
                    request_type=rt,
                    defaults={
                        'location': location,
                        'requester_user': user,
                        'assignee_user': user if i % 2 == 0 else None,
                        'priority': random.choice(['low', 'normal', 'high']),
                        'status': random.choice(['pending', 'in_progress', 'resolved']),
                        'notes': f'Demo service request #{i+1}'
                    }
                )
                if created or force:
                    sr.save()
            self.stdout.write(self.style.SUCCESS('Service requests seeded'))

        # Guest comments (feedback channel)
        if seed_reviews or not GuestComment.objects.exists():
            channels = ['web', 'mobile', 'kiosk']
            for i in range(8):
                gc, created = GuestComment.objects.get_or_create(
                    guest=guest,
                    channel=random.choice(channels),
                    defaults={
                        'source': 'demo',
                        'rating': random.choice([5,4,3,2,1]),
                        'comment_text': f'Demo comment {i+1}',
                        'created_at': now - datetime.timedelta(days=i)
                    }
                )
                if created or force:
                    gc.save()
            self.stdout.write(self.style.SUCCESS('Guest comments seeded'))

        self.stdout.write(self.style.SUCCESS('Demo data seeding completed.'))
