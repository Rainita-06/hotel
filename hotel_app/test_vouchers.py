from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import timedelta
from django.contrib.auth.models import User
from hotel_app.models import Voucher

class VoucherTestCase(TestCase):
    def setUp(self):
        # 1️⃣ Create a staff user
        self.staff_user = User.objects.create_user(username="staf", password="password123")
        self.client = Client()
        self.client.login(username="staf", password="password123")

        # 2️⃣ Create a sample voucher valid for today
        self.voucher = Voucher.objects.create(
            guest_name="John Doe",
            room_no="101",
            country_code="+91",
            phone_number="9876543210",
            email="john@example.com",
            adults=2,
            kids=1,
            quantity=1,
            check_in_date=timezone.localdate(),
            check_out_date=timezone.localdate() + timedelta(days=1),
            include_breakfast=True,
        )

        # 3️⃣ Add dummy QR code file
        self.voucher.qr_code_image.save(
            f'test_qr_{self.voucher.id}.png',
            ContentFile(b'Test QR content'),
            save=True
        )
        self.voucher.save()

    # ---------------- Create Voucher ----------------
    def test_create_voucher_checkin(self):
        url = reverse("checkin_form")  # Corrected
        data = {
            "guest_name": "Alice",
            "room_no": "102",
            "adults": 2,
            "kids": 0,
            "quantity": 1,
            "country_code": "+91",
            "phone_number": "9876543211",
            "email": "alice@example.com",
            "check_in_date": timezone.localdate().isoformat(),
            "check_out_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
            "include_breakfast": "on",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Voucher.objects.filter(guest_name="Alice").exists())
        voucher = Voucher.objects.get(guest_name="Alice")
        self.assertIsNotNone(voucher.qr_code_image)
        self.assertTrue(voucher.include_breakfast)

    # ---------------- Voucher Landing Page ----------------
    def test_voucher_landing_page(self):
        url = reverse("voucher_landing", args=[self.voucher.voucher_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.voucher.guest_name)

    # ---------------- Scan & Validate Voucher ----------------
    def test_validate_voucher_first_time(self):
        url = reverse("validate_voucher")
        response = self.client.get(url, {"code": self.voucher.voucher_code})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["redeemed"])
        self.assertEqual(data["scan_count"], 1)

    def test_validate_voucher_second_time(self):
        url = reverse("validate_voucher")
        self.client.get(url, {"code": self.voucher.voucher_code})
        response = self.client.get(url, {"code": self.voucher.voucher_code})
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("already used", data["message"].lower())

    # ---------------- Invalid Voucher ----------------
    def test_validate_invalid_voucher(self):
        url = reverse("validate_voucher")
        response = self.client.get(url, {"code": "INVALID123"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("invalid voucher code", response.json()["message"].lower())

    # ---------------- Expired Voucher ----------------
    def test_validate_expired_voucher(self):
        self.voucher.check_out_date = timezone.localdate() - timedelta(days=1)
        self.voucher.save()
        url = reverse("validate_voucher")
        response = self.client.get(url, {"code": self.voucher.voucher_code})
        self.assertEqual(response.status_code, 400)
        self.assertIn("expired", response.json()["message"].lower())

    # ---------------- Mark Checkout ----------------
    def test_mark_checkout(self):
        url = reverse("checkout", args=[self.voucher.id])  # Corrected
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        voucher = Voucher.objects.get(id=self.voucher.id)
        self.assertEqual(voucher.check_out_date, timezone.localdate())

    # ---------------- Breakfast Voucher Report Export ----------------
    def test_breakfast_voucher_report_export(self):
        url = reverse("breakfast_voucher_report") + "?export=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
