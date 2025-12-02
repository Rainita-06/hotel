from django.core.management.base import BaseCommand
from django.utils import timezone
import random
import re

from hotel_app.models import (
    Department,
    RequestType,
    DepartmentRequestSLA,
    TicketReview,
    ServiceRequest,
    Guest,
    Location,
    Voucher,
)

# ============================
# PASTE YOUR MAPPING HERE
# Each line: "<Department>\t<Request Type>"
# You provided a long mapping in your message. Paste it below (exactly)
# The generator will parse it. If you need to exclude other lines, add filters below.
# ============================
MAPPING_TEXT = """
Concierge\tRequest Payung
Concierge\tOpen Access Room
Concierge\tRequest Bellboy
Digital Marketing\tE-flyer
Digital Marketing\tSign
Digital Marketing\tFood tag
Engineering\tJet Spray Toilet
Engineering\tRel Curtain
Front Office\tKartu Kamar
Housekeeping\tRequest Sajadah
Housekeeping\tRequest Sarung
IT\tChannel tv
IT\tAplikasi
Laundry\tDelivery Laundry
Gardener\tTanaman
# ... paste the full list you provided here (each line Dept<TAB>ReqType)
"""

# lines with these substrings (case-insensitive) will be excluded — adjust if needed:
EXCLUDE_CONDITIONS = [
    lambda dept, req: dept.strip().lower() == "audio visual" and "sign tv" in req.strip().lower(),
    # add any other exclude rules here as lambda dept,req: ...
]


def parse_mapping(text):
    items = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Accept tab or multiple spaces or ' - ' separators
        parts = re.split(r"\t+|\s{2,}|\s*-\s*", line, maxsplit=1)
        if len(parts) < 2:
            continue
        dept = parts[0].strip()
        req = parts[1].strip()
        # exclusion filter
        skip = False
        for cond in EXCLUDE_CONDITIONS:
            try:
                if cond(dept, req):
                    skip = True
                    break
            except Exception:
                pass
        if skip:
            continue
        items.append((dept, req))
    return items


class Command(BaseCommand):
    help = "Generate sample data: departments/request-types + ServiceRequest tickets + TicketReview rows"

    def add_arguments(self, parser):
        parser.add_argument("--service-count", type=int, default=10, help="Number of ServiceRequest tickets to create")
        parser.add_argument("--review-count", type=int, default=10, help="Number of TicketReview rows to create (split matched/unmatched)")
        parser.add_argument("--matched-review-ratio", type=float, default=0.5, help="Fraction of reviews that are matched (0..1)")

    def handle(self, *args, **options):
        service_count = options["service_count"]
        review_count = options["review_count"]
        matched_ratio = float(options["matched_review_ratio"])

        mapping = parse_mapping(MAPPING_TEXT)
        if not mapping:
            self.stdout.write(self.style.ERROR("❌ No mapping entries found. Paste mapping into MAPPING_TEXT."))
            return

        # Create Departments and RequestTypes (or get existing)
        created_depts = {}
        created_rts = {}

        for dept_name, req_name in mapping:
            dept_obj, _ = Department.objects.get_or_create(name=dept_name)
            rt_obj, _ = RequestType.objects.get_or_create(name=req_name, defaults={"active": True})
            # create/ensure SLA mapping so views that use DepartmentRequestSLA can map request_type -> department
            try:
                DepartmentRequestSLA.objects.get_or_create(request_type=rt_obj, department=dept_obj)
            except Exception:
                # If the model isn't present or constraint fails, continue gracefully
                pass
            created_depts[dept_name] = dept_obj
            created_rts[req_name] = rt_obj

        self.stdout.write(self.style.SUCCESS(f"✔ Prepared {len(created_depts)} departments and {len(created_rts)} request types."))

        # Ensure a Guest & Location exist to attach tickets to (use or create demo ones)
        guest, _ = Guest.objects.get_or_create(
            full_name="Demo Guest",
            defaults={"email": "guest@example.com", "phone": "9998887770", "room_number": "101"}
        )
        # Try Location, Voucher: keep optional to avoid hard failure
        try:
            location, _ = Location.objects.get_or_create(name="Demo Room 101", defaults={"room_no": "101"})
        except Exception:
            location = None

        # ---------- Create ServiceRequest tickets ----------
        self.stdout.write("\n➡ Creating ServiceRequest tickets...")
        dept_list = list(created_depts.values())
        rt_list = list(created_rts.values())

        for i in range(service_count):
            # Randomly decide whether to assign a request_type or leave unclassified
            assign_type = random.random() > 0.25  # 75% classified, 25% unclassified
            req_type = random.choice(rt_list) if (assign_type and rt_list) else None
            dept = None
            if req_type:
                # Prefer DepartmentRequestSLA if available
                try:
                    sla = DepartmentRequestSLA.objects.filter(request_type=req_type).first()
                    if sla and sla.department:
                        dept = sla.department
                    else:
                        dept = random.choice(dept_list) if dept_list else None
                except Exception:
                    dept = random.choice(dept_list) if dept_list else None
            else:
                dept = random.choice(dept_list) if dept_list else None

            notes = f"Auto-generated ServiceRequest #{i+1} - sample"
            ticket_kwargs = {
                "notes": notes,
                "status": "pending",
                "priority": random.choice(["normal", "high", "low"]),
                "created_at": timezone.now(),
            }
            # attach optional FK fields safely
            if req_type:
                ticket_kwargs["request_type"] = req_type
            if dept:
                ticket_kwargs["department"] = dept
            if guest:
                # some ServiceRequest models use 'guest' FK or 'guest_name'; try both safely
                try:
                    ticket_kwargs["guest"] = guest
                except Exception:
                    ticket_kwargs["guest_name"] = getattr(guest, "full_name", "Demo Guest")
                # try setting a location or room
                try:
                    ticket_kwargs["room_no"] = guest.room_number
                except Exception:
                    pass

            # Creating ServiceRequest; use flexible creation to handle model field name differences
            try:
                ticket = ServiceRequest.objects.create(**ticket_kwargs)
                self.stdout.write(self.style.SUCCESS(f"✔ ServiceRequest #{ticket.pk} created (req_type={'None' if not req_type else req_type.name})"))
            except Exception as e:
                # fallback: try minimal fields
                try:
                    ticket = ServiceRequest.objects.create(notes=notes, status="pending", priority="normal")
                    self.stdout.write(self.style.SUCCESS(f"✔ (fallback) ServiceRequest #{ticket.pk} created"))
                except Exception as ex:
                    self.stdout.write(self.style.WARNING(f"⚠ Failed to create ServiceRequest #{i+1}: {ex}"))

        # ---------- Create TicketReview rows ----------
        self.stdout.write("\n➡ Creating TicketReview rows...")
        matched_target = int(review_count * matched_ratio)
        unmatched_target = review_count - matched_target

        # matched reviews
        for i in range(matched_target):
            rt = random.choice(rt_list) if rt_list else None
            dept = None
            if rt:
                try:
                    sla = DepartmentRequestSLA.objects.filter(request_type=rt).first()
                    dept = sla.department if sla and sla.department else random.choice(dept_list) if dept_list else None
                except Exception:
                    dept = random.choice(dept_list) if dept_list else None

            review_text = f"Matched review message #{i+1} - auto"
            try:
                review = TicketReview.objects.create(
                    voucher=None,
                    guest_name=guest.full_name if guest else "Guest",
                    room_no=getattr(guest, "room_number", "101"),
                    phone_number=getattr(guest, "phone", "9998887770"),
                    request_text=review_text,
                    matched_request_type=rt,
                    matched_department=dept,
                    match_confidence=round(random.uniform(0.7, 0.98), 2),
                    is_matched=True,
                    priority=random.choice(["normal", "high"]),
                    moved_to_ticket=False,
                    created_at=timezone.now(),
                )
                self.stdout.write(self.style.SUCCESS(f"✔ TicketReview #{review.pk} (matched) created"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Failed to create matched TicketReview #{i+1}: {e}"))

        # unmatched reviews
        for i in range(unmatched_target):
            review_text = f"Unmatched review message #{i+1} - auto"
            try:
                review = TicketReview.objects.create(
                    voucher=None,
                    guest_name=None,
                    room_no=None,
                    phone_number=f"999900{random.randint(1000,9999)}",
                    request_text=review_text,
                    matched_request_type=None,
                    matched_department=None,
                    match_confidence=round(random.uniform(0.0, 0.4), 2),
                    is_matched=False,
                    priority="normal",
                    moved_to_ticket=False,
                    created_at=timezone.now(),
                )
                self.stdout.write(self.style.SUCCESS(f"✔ TicketReview #{review.pk} (unmatched) created"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠ Failed to create unmatched TicketReview #{i+1}: {e}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 Done. ServiceRequest and TicketReview sample data created."))


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
def generate_member_qr(member):
    """
    Generate QR code that matches the EXACT logic used in your gym QR scanner.
    Format: GYM-MEMBER:{customer_code}
    """
    qr_data = f"GYM-MEMBER:{member.customer_code}"

    qr_img = qrcode.make(qr_data)

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")

    file_name = f"qr_{member.customer_code}.png"
    member.qr_code_image.save(file_name, ContentFile(buffer.getvalue()), save=True)


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
        self.stdout.write(self.style.SUCCESS("\n🎉 SEEDING COMPLETE\n"))
        for key, val in created_counts.items():
            self.stdout.write(f"  ✔ {key}: {val}")

