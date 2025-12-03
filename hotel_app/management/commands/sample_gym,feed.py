# hotel_app/management/commands/seed_demo_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.conf import settings

import qrcode
import random
import io
import os
from datetime import timedelta

from hotel_app.models import (
    GymMember,
    GymVisit,
    Voucher,
    Review,
    Guest,  # optional - used if you want to link reviews to guests
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

QR_SUBFOLDER = "qr_codes"


def _safe_int_from_code(code, prefix):
    """Return integer suffix if possible, else None."""
    try:
        return int(code.replace(prefix, ""))
    except Exception:
        return None


def _next_customer_code():
    """
    Find the maximum numeric suffix used in existing GymMember.customer_code and return the next code.
    This avoids collisions if older (non-standard) customer_code values exist.
    """
    prefix = "FGS"
    last_member = GymMember.objects.order_by("-member_id").first()
    max_n = 0
    # scan all existing codes to be safe (efficient enough for demo sizes).
    for m in GymMember.objects.exclude(customer_code__isnull=True).exclude(customer_code=""):
        val = _safe_int_from_code(getattr(m, "customer_code", ""), prefix)
        if val and val > max_n:
            max_n = val
    # also check last_member numeric if present
    if last_member and getattr(last_member, "customer_code", None):
        val = _safe_int_from_code(last_member.customer_code, prefix)
        if val and val > max_n:
            max_n = val
    next_num = max_n + 1
    return f"{prefix}{next_num:04d}"


def _generate_voucher_code():
    """Safer voucher code generator — ensures uniqueness by checking DB."""
    prefix = "BKT"
    for _ in range(10):
        code = f"{prefix}{random.randint(100000, 999999)}"
        if not Voucher.objects.filter(voucher_code=code).exists():
            return code
    # fallback, use timestamp-like
    return f"{prefix}{int(timezone.now().timestamp())}"


def _ensure_qr_folder():
    folder = os.path.join(getattr(settings, "MEDIA_ROOT", ""), QR_SUBFOLDER)
    os.makedirs(folder, exist_ok=True)
    return folder


def generate_member_qr(member):
    """
    Generate and save PNG QR image to member.qr_code_image (ImageField).
    This function is defensive: it doesn't overwrite existing QR unless necessary.
    """
    if not member or not getattr(member, "customer_code", None):
        return

    qr_data = f"GYM-MEMBER:{member.customer_code}"
    qr_img = qrcode.make(qr_data)

    buffer = io.BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)

    file_name = f"member_{member.customer_code}.png"
    # Ensure subfolder exists in MEDIA
    _ensure_qr_folder()
    # Save file to the model's ImageField. save() may generate storage path based on ImageField upload_to.
    member.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)


class Command(BaseCommand):
    help = "Seed demo data: gym members, visits, vouchers, reviews. (Does not delete existing data.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=15,
            help="How many members/visits/vouchers/reviews to create (default: 15)",
        )
        parser.add_argument(
            "--force-qr",
            action="store_true",
            help="Regenerate QR for created members even if they already have a qr image",
        )

    def handle(self, *args, **options):
        count = max(1, int(options.get("count", 15)))
        force_qr = bool(options.get("force_qr", False))

        created_counts = {"members": 0, "visits": 0, "vouchers": 0, "reviews": 0}

        with transaction.atomic():
            # create or append members
            created_members = []
            for _ in range(count):
                first = random.choice(SAMPLE_FIRST_NAMES)
                last = random.choice(SAMPLE_LAST_NAMES)
                full_name = f"{first} {last}"

                # generate a customer_code that does not clash
                customer_code = _next_customer_code()

                # If a member with this exact name and email exists, skip duplication.
                email = f"member{random.randint(1000,9999)}@example.com"

                member, created = GymMember.objects.get_or_create(
                    customer_code=customer_code,
                    defaults={
                        "full_name": full_name,
                        "nik": f"NIK{random.randint(10000,99999)}",
                        "address": f"{random.randint(10,200)} {random.choice(['1st St','MG Road','Park Lane'])}",
                        "city": random.choice(SAMPLE_CITIES),
                        "place_of_birth": random.choice(SAMPLE_CITIES),
                        "date_of_birth": (timezone.now().date() - timedelta(days=random.randint(20*365, 45*365))),
                        "religion": random.choice(["Hindu", "Muslim", "Christian", "Sikh", "Other"]),
                        "gender": random.choice(["Male", "Female"]),
                        "occupation": random.choice(SAMPLE_OCCUPATIONS),
                        "phone": f"9{random.randint(700000000, 999999999)}",
                        "email": email,
                        "pin": str(random.randint(1000,9999)),
                        "start_date": timezone.now().date() - timedelta(days=random.randint(0,10)),
                        "expiry_date": timezone.now().date() + timedelta(days=120),
                        "status": "Active",
                    },
                )

                # Generate QR only if missing or forced
                if force_qr or not getattr(member, "qr_code_image", None) or not member.qr_code_image:
                    try:
                        generate_member_qr(member)
                    except Exception as e:
                        # don't abort seeding for QR failure, log to stdout
                        self.stdout.write(self.style.WARNING(f"QR generation failed for {member}: {e}"))

                created_members.append(member)
                if created:
                    created_counts["members"] += 1

            # Create visits for members (append-only)
            superuser = User.objects.filter(is_superuser=True).first()
            for member in created_members:
                visit_time = timezone.now() - timedelta(days=random.randint(0,5), hours=random.randint(0,12))
                # create a visit entry (avoid duplicates by unique combination of member+visit_at within minute)
                exists = GymVisit.objects.filter(member=member, visit_at__date=visit_time.date()).exists()
                if not exists:
                    GymVisit.objects.create(
                        member=member,
                        visitor=None,
                        visit_at=visit_time,
                        checked_by_user=superuser,
                        notes=random.choice(["Morning workout", "Evening cardio", "Personal training session", "Weights training", "Crossfit routine"])
                    )
                    created_counts["visits"] += 1

            # Create vouchers (get_or_create by voucher_code to avoid duplicates)
            for i in range(count):
                guest = f"{random.choice(SAMPLE_FIRST_NAMES)} {random.choice(SAMPLE_LAST_NAMES)}"
                voucher_code = _generate_voucher_code()

                # Use get_or_create so existing vouchers aren't overwritten
                voucher, v_created = Voucher.objects.get_or_create(
                    voucher_code=voucher_code,
                    defaults={
                        "guest_name": guest,
                        "room_no": str(100 + i),
                        "country_code": "91",
                        "phone_number": f"9{random.randint(700000000, 999999999)}",
                        "check_in_date": timezone.now().date(),
                        "check_out_date": timezone.now().date() + timedelta(days=1),
                        "expiry_date": timezone.now().date() + timedelta(days=7),
                        "redeemed": False,
                        "qr_code": f"VOUCHER-{voucher_code}",
                    },
                )
                if v_created:
                    # if your Voucher model has ImageField for qr_code_image, generate and save it.
                    try:
                        if hasattr(voucher, "qr_code_image"):
                            qr = qrcode.make(voucher.voucher_code)
                            buf = io.BytesIO()
                            qr.save(buf, format="PNG")
                            buf.seek(0)
                            fname = f"voucher_{voucher.voucher_code}.png"
                            voucher.qr_code_image.save(fname, ContentFile(buf.getvalue()), save=True)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Voucher QR save failed: {e}"))
                    created_counts["vouchers"] += 1

            # Create reviews (append-only)
            for _ in range(count):
                rating = random.randint(1, 5)
                comment = random.choice(SAMPLE_COMMENTS)
                created_at = timezone.now() - timedelta(days=random.randint(0, 10))
                # use create (reviews can be duplicates) — if you prefer unique, use get_or_create with guest/email
                Review.objects.create(rating=rating, comment=comment, created_at=created_at)
                created_counts["reviews"] += 1

        # Summary
        self.stdout.write(self.style.SUCCESS("SEEDING COMPLETE"))
        for key, val in created_counts.items():
            self.stdout.write(f"  {key}: {val}")

        # self.stdout.write(self.style.NOTICE("Note: existing data is preserved. Use --force-qr to regenerate QR images."))
