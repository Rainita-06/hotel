
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import qrcode
import random
from io import BytesIO
from datetime import timedelta

from hotel_app.models import (
    GymMember,
    GymVisit,
    Voucher,
    Review,
)

User = get_user_model()

SAMPLE_FIRST_NAMES = [
    "Aarav","Vivaan","Aditya","Vihaan","Arjun","Isha","Diya","Ananya","Ridhi","Neha",
    "Rahul","Priya","Siddharth","Karan","Meera","Rohit","Simran","Nikhil","Pooja","Sana"
]
SAMPLE_LAST_NAMES = ["Sharma","Verma","Kumar","Singh","Patel","Gupta","Reddy","Iyer","Nair","Das"]
SAMPLE_CITIES = ["Bangalore","Mumbai","Delhi","Chennai","Kolkata","Hyderabad","Pune"]
SAMPLE_OCCUPATIONS = ["Engineer","Teacher","Designer","Doctor","Student","Manager"]
SAMPLE_COMMENTS = [
    "Great service and clean gym facilities.",
    "Staff were helpful but machines need maintenance.",
    "Towels were not available on arrival.",
    "Excellent trainer session — very motivating.",
    "Wifi in the gym was unstable.",
    "Good timing and well kept place.",
    "Locker space insufficient during peak hours.",
    "Happy with overall experience.",
    "Could improve the air conditioning.",
    "Breakfast buffet was tasty and fresh."
]

# ------------------------------------------------------
# VALID QR GENERATOR → URL BASED
# ------------------------------------------------------
import os
from django.conf import settings
def generate_member_qr(member):
    qr_data = f"GYM-MEMBER:{member.customer_code}"
    qr_img = qrcode.make(qr_data)

    qr_folder = os.path.join(settings.MEDIA_ROOT, "qr_codes")
    os.makedirs(qr_folder, exist_ok=True)  # <–– FIX

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")

    file_name = f"qr_{member.customer_code}.png"
    member.qr_code_image.save(
        file_name,
        ContentFile(buffer.getvalue()),
        save=True
    )


# ------------------------------------------------------
# INCREMENTAL CUSTOMER CODE
# ------------------------------------------------------
def _generate_customer_code():
    last = GymMember.objects.order_by("-member_id").first()
    if last and getattr(last, "customer_code", None):
        try:
            number = int(last.customer_code.replace("FGS", ""))
            number += 1
        except:
            number = GymMember.objects.count() + 1
    else:
        number = GymMember.objects.count() + 1
    return f"FGS{number:04d}"

# ------------------------------------------------------
# BREAKFAST VOUCHER CODE
# ------------------------------------------------------
def _generate_voucher_code():
    try:
        from hotel_app.models import random_code
        return random_code(prefix="BKT", length=6)
    except:
        return f"BKT{random.randint(100000,999999)}"

# ------------------------------------------------------
# MAIN COMMAND
# ------------------------------------------------------
class Command(BaseCommand):
    help = "Seed demo data: 15 Members, 15 Visits, 15 Vouchers, 15 Reviews"

    def handle(self, *args, **options):

        created_counts = {
            "members": 0,
            "visits": 0,
            "vouchers": 0,
            "reviews": 0
        }

        with transaction.atomic():

            # ------------------------------------------------------
            # (1) CREATE 15 GYM MEMBERS + QR
            # ------------------------------------------------------
            members = []
            for _ in range(15):
                first = random.choice(SAMPLE_FIRST_NAMES)
                last = random.choice(SAMPLE_LAST_NAMES)

                full_name = f"{first} {last}"
                customer_code = _generate_customer_code()

                member = GymMember.objects.create(
                    customer_code=customer_code,
                    full_name=full_name,
                    nik=f"NIK{random.randint(10000,99999)}",
                    address=f"{random.randint(10,200)} {random.choice(['1st St','MG Road','Park Lane'])}",
                    city=random.choice(SAMPLE_CITIES),
                    place_of_birth=random.choice(SAMPLE_CITIES),
                    date_of_birth=timezone.now().date()
                        - timedelta(days=random.randint(20*365, 45*365)),
                    religion=random.choice(["Hindu","Muslim","Christian","Sikh","Other"]),
                    gender=random.choice(["Male","Female"]),
                    occupation=random.choice(SAMPLE_OCCUPATIONS),
                    phone=f"9{random.randint(700000000, 999999999)}",
                    email=f"member{random.randint(1000,9999)}@example.com",
                    pin=str(random.randint(1000,9999)),
                    start_date=timezone.now().date() - timedelta(days=random.randint(0,10)),
                    expiry_date=timezone.now().date() + timedelta(days=120),
                    status="Active",
                )

                generate_member_qr(member)

                members.append(member)
                created_counts["members"] += 1

            # ------------------------------------------------------
            # (2) CREATE 15 GYM VISITS
            # ------------------------------------------------------
            for member in members:
                visit_time = timezone.now() - timedelta(
                    days=random.randint(0,5),
                    hours=random.randint(0,12)
                )

                GymVisit.objects.create(
                    member=member,
                    visitor=None,
                    visit_at=visit_time,
                    checked_by_user=User.objects.filter(is_superuser=True).first(),
                    notes=random.choice([
                        "Morning workout",
                        "Evening cardio",
                        "Personal training session",
                        "Weights training",
                        "Crossfit routine"
                    ])
                )

                created_counts["visits"] += 1

            # ------------------------------------------------------
            # (3) CREATE 15 BREAKFAST VOUCHERS
            # ------------------------------------------------------
            for i in range(1, 16):
                guest = f"{random.choice(SAMPLE_FIRST_NAMES)} {random.choice(SAMPLE_LAST_NAMES)}"
                voucher_code = _generate_voucher_code()

                Voucher.objects.create(
                    voucher_code=voucher_code,
                    guest_name=guest,
                    room_no=str(100 + i),
                    country_code="91",
                    phone_number=f"9{random.randint(700000000, 999999999)}",
                    check_in_date=timezone.now().date(),
                    check_out_date=timezone.now().date() + timedelta(days=1),
                    expiry_date=timezone.now().date() + timedelta(days=7),
                    redeemed=False,
                    qr_code=f"VOUCHER-{voucher_code}",
                )

                created_counts["vouchers"] += 1

            # ------------------------------------------------------
            # (4) CREATE 15 REVIEWS
            # ------------------------------------------------------
            for _ in range(15):
                Review.objects.create(
                    rating=random.randint(1, 5),
                    comment=random.choice(SAMPLE_COMMENTS),
                    created_at=timezone.now() - timedelta(days=random.randint(0,10))
                )

                created_counts["reviews"] += 1

        # ------------------------------------------------------
        # DONE
        # ------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n SEEDING COMPLETE\n"))
        for key, val in created_counts.items():
            self.stdout.write(f"   {key}: {val}")