"""Simplified script to populate test data for dashboard statistics"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotel_app.models import ServiceRequest, GymMember, Guest, Department
from django.utils import timezone
from datetime import timedelta
import random

today = timezone.now()
print("Populating dashboard test data...\n")

# Get existing department or use first available
department = Department.objects.first()
if not department:
    department = Department.objects.create(name='Housekeeping')
    print(f"Created department: {department.name}")
else:
    print(f"Using department: {department.name}")

print("\n=== Creating Service Requests ===")
# Check if we already have service requests
existing_count = ServiceRequest.objects.count()
if existing_count > 0:
    print(f"Found {existing_count} existing service requests")
    # Update some to be completed for staff efficiency calculation
    pending_requests = ServiceRequest.objects.filter(status='pending')[:15]
    for i, sr in enumerate(pending_requests):
        completed_at = today - timedelta(days=random.randint(1, 29))
        sr.status = 'completed'
        sr.completed_at = completed_at
        # 80% should meet SLA
        sr.resolution_sla_breached = random.random() > 0.8
        sr.save()
        print(f"Updated ServiceRequest #{sr.id} - SLA {'BREACHED' if sr.resolution_sla_breached else 'MET'}")
else:
    print("No existing service requests found. Staff Efficiency will remain 0%")

print(f"\n=== Creating GYM Members ===")
# Create some active gym members
for i in range(25):
    expiry_date = today.date() + timedelta(days=random.randint(30, 365))
    customer_code = f'GYM{1000+i}'
    
    # Check if already exists
    if GymMember.objects.filter(customer_code=customer_code).exists():
        print(f"GymMember {customer_code} already exists, skipping")
        continue
    
    gm = GymMember.objects.create(
        customer_code=customer_code,
        full_name=f'Gym Member {i+1}',
        email=f'gymmember{i+1}@example.com',
        phone=f'5551001{i:03d}',  # 10 digits
        address=f'{i+1} Main Street',
        password='testpass123',
        confirm_password='testpass123',
        status='Active',
        plan_type='Monthly' if i % 2 == 0 else 'Annual',
        start_date=today.date() - timedelta(days=random.randint(1, 90)),
        expiry_date=expiry_date
    )
    print(f"Created GymMember: {gm.full_name} (expires: {expiry_date})")

# Create a few expired gym members (should not be counted)
for i in range(3):
    expiry_date = today.date() - timedelta(days=random.randint(1, 30))
    customer_code = f'EXP{2000+i}'
    
    if GymMember.objects.filter(customer_code=customer_code).exists():
        continue
    
    gm = GymMember.objects.create(
        customer_code=customer_code,
        full_name=f'Expired Member {i+1}',
        email=f'expired{i+1}@example.com',
        phone=f'5552001{i:03d}',  # 10 digits
        address=f'{i+1} Expired Lane',
        password='testpass123',
        confirm_password='testpass123',
        status='Active',
        plan_type='Monthly',
        start_date=today.date() - timedelta(days=365),
        expiry_date=expiry_date
    )
    print(f"Created Expired GymMember: {gm.full_name} (expired: {expiry_date})")

print(f"\n=== Creating Guests ===")
# Create some currently checked-in guests
for i in range(42):
    checkin_date = today.date() - timedelta(days=random.randint(0, 5))
    checkout_date = today.date() + timedelta(days=random.randint(1, 7))
    
    # Check if guest with this email already exists
    email = f'guest{i+1}@example.com'
    if Guest.objects.filter(email=email).exists():
        print(f"Guest {email} already exists, skipping")
        continue
    
    guest = Guest.objects.create(
        full_name=f'Guest {i+1}',
        email=email,
        phone=f'555-{3000+i}',
        room_number=f'{100+i}',
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        checkin_datetime=timezone.make_aware(timezone.datetime.combine(checkin_date, timezone.datetime.min.time())),
        checkout_datetime=timezone.make_aware(timezone.datetime.combine(checkout_date, timezone.datetime.min.time())),
    )
    print(f"Created Guest: {guest.full_name} (Room {guest.room_number})")

# Create some guests who have already checked out
for i in range(10):
    checkin_date = today.date() - timedelta(days=random.randint(8, 30))
    checkout_date = today.date() - timedelta(days=random.randint(1, 7))
    
    email = f'pastguest{i+1}@example.com'
    if Guest.objects.filter(email=email).exists():
        continue
    
    guest = Guest.objects.create(
        full_name=f'Past Guest {i+1}',
        email=email,
        phone=f'555-{4000+i}',
        room_number=f'{200+i}',
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        checkin_datetime=timezone.make_aware(timezone.datetime.combine(checkin_date, timezone.datetime.min.time())),
        checkout_datetime=timezone.make_aware(timezone.datetime.combine(checkout_date, timezone.datetime.min.time())),
    )

print("\n" + "="*60)
print("✓ Test data created successfully!")
print("="*60)

# Show final counts
completed_requests = ServiceRequest.objects.filter(
    completed_at__isnull=False,
    completed_at__gte=today - timedelta(days=30)
)
staff_efficiency = int(round((completed_requests.filter(resolution_sla_breached=False).count() / completed_requests.count() * 100))) if completed_requests.count() > 0 else 0

active_gym = GymMember.objects.filter(status="Active").exclude(expiry_date__lt=today.date()).count()
active_guests = Guest.objects.filter(checkin_date__lte=today.date(), checkout_date__gte=today.date()).count()

print(f"\nDashboard will now show:")
print(f"  • Staff Efficiency: {staff_efficiency}%")
print(f"  • Active GYM Members: {active_gym}")
print(f"  • Active Guests: {active_guests}")
print("\nRefresh your dashboard to see the changes!")
