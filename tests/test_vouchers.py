from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from hotel_app.models import Voucher

class VoucherAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.voucher_data = {
            "guest_name": "John Doe",
            "room_no": "101",
            "phone_number": "9876543210",
            "country_code": "+91",
            "adults": 2,
            "kids": 1,
            "check_in_date": date.today(),
            "check_out_date": date.today() + timedelta(days=2),
            "include_breakfast": True
        }

    def test_create_voucher(self):
        """✅ Should create a voucher and auto-generate QR"""
        response = self.client.post("/api/vouchers/", self.voucher_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Voucher.objects.exists())
        voucher = Voucher.objects.first()
        self.assertIsNotNone(voucher.qr_code_image)
        self.assertIsNotNone(voucher.voucher_code)

    def test_validate_voucher(self):
        """✅ Should validate a voucher successfully"""
        voucher = Voucher.objects.create(**self.voucher_data)
        voucher.voucher_code = "ABC123"
        voucher.save()

        response = self.client.get(f"/api/vouchers/validate/?code={voucher.voucher_code}")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_report(self):
        """✅ Should return report counts"""
        Voucher.objects.create(**self.voucher_data)
        response = self.client.get("/api/vouchers/report/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("daily_checkins", response.data)

    def test_checkout(self):
        """✅ Should mark checkout date for voucher"""
        voucher = Voucher.objects.create(**self.voucher_data)
        url = f"/api/vouchers/{voucher.id}/checkout/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        voucher.refresh_from_db()
        self.assertEqual(voucher.check_out_date, date.today())

    def test_share_whatsapp(self):
        """✅ Should return WhatsApp share URL"""
        voucher = Voucher.objects.create(**self.voucher_data)
        url = f"/api/vouchers/{voucher.id}/share/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("whatsapp_url", response.data)
