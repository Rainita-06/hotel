from django.core.management.base import BaseCommand
from django.utils import timezone
from hotel_app.models import (
    ServiceRequest,
    TicketReview,
    UnmatchedRequest,
    RequestType,
    Department,
    Voucher
)
import random


class Command(BaseCommand):
    help = "Generate Normal, Matched, Unmatched TicketReview and UnmatchedRequest tickets"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Generating sample tickets...\n")

        # ---- Load required data ----
        request_types = list(RequestType.objects.filter(active=True))
        departments = list(Department.objects.all())
        vouchers = list(Voucher.objects.all())

        if not request_types or not departments:
            self.stdout.write(self.style.ERROR(
                "❌ RequestTypes and Departments must exist before running this!"
            ))
            return

        # ------------------------------------------------------
        # 1️⃣ CREATE 10 NORMAL TICKETS (ServiceRequest)
        # ------------------------------------------------------
        for _ in range(10):
            rt = random.choice(request_types)
            dept = random.choice(departments)
            normal_ticket = ServiceRequest.objects.create(
                request_type=rt,
                department=dept,
                priority="normal",
                status="pending",
                notes="Auto-generated NORMAL ticket",
                created_at=timezone.now(),
            )
            self.stdout.write(self.style.SUCCESS(
                f"✅ Normal Ticket Created → ID {normal_ticket.pk}"
            ))

        # ------------------------------------------------------
        # 2️⃣ CREATE 10 TicketReview tickets (5 matched + 5 unmatched)
        # ------------------------------------------------------
        for i in range(10):
            rt = random.choice(request_types)
            dept = random.choice(departments)
            voucher = random.choice(vouchers) if vouchers else None

            if i < 5:
                # Matched TicketReview
                matched_review = TicketReview.objects.create(
                    voucher=voucher,
                    guest_name=voucher.guest_name if voucher else f"Guest{i+1}",
                    room_no=voucher.room_no if voucher else f"{100+i}",
                    phone_number=voucher.phone_number if voucher else f"99999999{i+1}",
                    request_text=f"Request #{i+1} - Extra towels",
                    matched_request_type=rt,
                    matched_department=dept,
                    match_confidence=0.90,
                    is_matched=True,
                    priority="normal",
                )
                self.stdout.write(self.style.SUCCESS(
                    f"🎯 Matched Review Created → ID {matched_review.pk}"
                ))
            else:
                # Unmatched TicketReview
                unmatched_review = TicketReview.objects.create(
                    voucher=voucher,
                    guest_name=voucher.guest_name if voucher else f"Guest{i+1}",
                    room_no=voucher.room_no if voucher else f"{100+i}",
                    phone_number=voucher.phone_number if voucher else f"88888888{i+1}",
                    request_text=f"Request #{i+1} - Something else",
                    matched_request_type=None,
                    matched_department=None,
                    match_confidence=0.0,
                    is_matched=False,
                    priority="normal",
                )
                self.stdout.write(self.style.SUCCESS(
                    f"📝 Unmatched Review Created → ID {unmatched_review.pk}"
                ))

        

            

        self.stdout.write(self.style.SUCCESS("\n🎉 DONE — All sample tickets created successfully!"))
