"""Script to check dashboard data and optionally create test data"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from hotel_app.models import ServiceRequest, GymMember, Guest
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
thirty_days_ago = today - timedelta(days=30)

# Check ServiceRequest data
completed_requests = ServiceRequest.objects.filter(
    completed_at__isnull=False,
    completed_at__gte=timezone.now() - timedelta(days=30)
)
print(f"\n=== SERVICE REQUESTS ===")
print(f"Total completed in last 30 days: {completed_requests.count()}")
print(f"Met SLA: {completed_requests.filter(resolution_sla_breached=False).count()}")
print(f"Breached SLA: {completed_requests.filter(resolution_sla_breached=True).count()}")

# Check GymMember data
active_gym_members = GymMember.objects.filter(status="Active").exclude(expiry_date__lt=today)
print(f"\n=== GYM MEMBERS ===")
print(f"Total GymMembers: {GymMember.objects.count()}")
print(f"Active (not expired): {active_gym_members.count()}")
print(f"With status='Active': {GymMember.objects.filter(status='Active').count()}")

# Check Guest data
active_guests = Guest.objects.filter(
    checkin_date__lte=today,
    checkout_date__gte=today
)
print(f"\n=== GUESTS ===")
print(f"Total Guests: {Guest.objects.count()}")
print(f"Active today: {active_guests.count()}")
print(f"Checked in today: {Guest.objects.filter(checkin_date=today).count()}")

print("\n" + "="*50)
print("Dashboard should show:")
print(f"Staff Efficiency: {int(round((completed_requests.filter(resolution_sla_breached=False).count() / completed_requests.count() * 100))) if completed_requests.count() > 0 else 0}%")
print(f"Active GYM Members: {active_gym_members.count()}")
print(f"Active Guests: {active_guests.count()}")
