"""Script to add test guests who are currently checked in"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotel_app.models import Guest
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
print(f"Adding test guests (today is {today})...\n")

# Clear existing test guests to avoid duplicates
Guest.objects.filter(email__contains='testguest').delete()
print("Cleared previous test guests")

# Create 42 guests who are currently checked in
print("\nCreating currently checked-in guests:")
for i in range(1, 43):
    # Checked in 0-5 days ago, checking out 1-7 days from now
    checkin_days_ago = i % 6  # 0 to 5 days
    checkout_days_ahead = (i % 7) + 1  # 1 to 7 days
    
    checkin_date = today - timedelta(days=checkin_days_ago)
    checkout_date = today + timedelta(days=checkout_days_ahead)
    
    guest = Guest.objects.create(
        full_name=f'Active Guest {i}',
        email=f'testguest{i}@example.com',
        phone=f'55{30000000+i}',  # 10+ digits
        room_number=f'{100+i}',
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        checkin_datetime=timezone.make_aware(
            timezone.datetime.combine(checkin_date, timezone.datetime.min.time())
        ),
        checkout_datetime=timezone.make_aware(
            timezone.datetime.combine(checkout_date, timezone.datetime.min.time())
        ),
    )
    print(f"✓ {guest.full_name} - Room {guest.room_number} (checked in {checkin_days_ago} days ago, checking out in {checkout_days_ahead} days)")

# Create 10 guests who have already checked out (should NOT be counted)
print("\nCreating past guests (already checked out):")
for i in range(1, 11):
    checkin_date = today - timedelta(days=15 + i)
    checkout_date = today - timedelta(days=i)
    
    guest = Guest.objects.create(
        full_name=f'Past Guest {i}',
        email=f'pastguest{i}@example.com',
        phone=f'55{40000000+i}',
        room_number=f'{200+i}',
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        checkin_datetime=timezone.make_aware(
            timezone.datetime.combine(checkin_date, timezone.datetime.min.time())
        ),
        checkout_datetime=timezone.make_aware(
            timezone.datetime.combine(checkout_date, timezone.datetime.min.time())
        ),
    )
    print(f"✓ {guest.full_name} - Checked out {i} days ago (should NOT be counted)")

# Create 5 future guests (not yet checked in, should NOT be counted)
print("\nCreating future guests (not yet checked in):")
for i in range(1, 6):
    checkin_date = today + timedelta(days=i)
    checkout_date = today + timedelta(days=i + 7)
    
    guest = Guest.objects.create(
        full_name=f'Future Guest {i}',
        email=f'futureguest{i}@example.com',
        phone=f'55{50000000+i}',
        room_number=f'{300+i}',
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        checkin_datetime=timezone.make_aware(
            timezone.datetime.combine(checkin_date, timezone.datetime.min.time())
        ),
        checkout_datetime=timezone.make_aware(
            timezone.datetime.combine(checkout_date, timezone.datetime.min.time())
        ),
    )
    print(f"✓ {guest.full_name} - Checking in in {i} days (should NOT be counted)")

print("\n" + "="*70)
print("✓ Test data created successfully!")
print("="*70)

# Verify the count
from django.db.models import Q
active_guests = Guest.objects.filter(
    Q(checkin_date__lte=today, checkout_date__gte=today) |
    Q(checkin_datetime__date__lte=today, checkout_datetime__date__gte=today)
).count()

print(f"\nActive Guests Count: {active_guests}")
print(f"Expected: 42 (currently checked in)")
print(f"Total Guests in DB: {Guest.objects.count()}")
print(f"\nBreakdown:")
print(f"  - Currently checked in: {active_guests}")
print(f"  - Already checked out: {Guest.objects.filter(checkout_date__lt=today).count()}")
print(f"  - Future check-ins: {Guest.objects.filter(checkin_date__gt=today).count()}")
print("\nRefresh your dashboard to see the updated Active Guests count!")
