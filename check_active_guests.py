import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from hotel_app.models import Guest
from django.db.models import Q
from django.utils import timezone

today = timezone.now().date()

# Count active guests
active_guests = Guest.objects.filter(
    Q(checkin_date__lte=today, checkout_date__gte=today) |
    Q(checkin_datetime__date__lte=today, checkout_datetime__date__gte=today)
).count()

total_guests = Guest.objects.count()
past_guests = Guest.objects.filter(checkout_date__lt=today).count()
future_guests = Guest.objects.filter(checkin_date__gt=today).count()

print(f"Today: {today}")
print(f"\nActive Guests (currently checked in): {active_guests}")
print(f"Total Guests in database: {total_guests}")
print(f"Past guests (checked out): {past_guests}")
print(f"Future guests (not yet checked in): {future_guests}")
