# from django.test import TestCase, Client
# from django.urls import reverse
# from django.utils import timezone
# from django.core.files.base import ContentFile
# from datetime import timedelta
# from django.contrib.auth.models import User
# from hotel_app.models import Voucher

# class VoucherTestCase(TestCase):
#     def setUp(self):
#         # 1️⃣ Create a staff user
#         self.staff_user = User.objects.create_user(username="staf", password="password123")
#         self.client = Client()
#         self.client.login(username="staf", password="password123")

#         # 2️⃣ Create a sample voucher valid for today
#         self.voucher = Voucher.objects.create(
#             guest_name="John Doe",
#             room_no="101",
#             country_code="+91",
#             phone_number="9876543210",
#             email="john@example.com",
#             adults=2,
#             kids=1,
#             quantity=1,
#             check_in_date=timezone.localdate(),
#             check_out_date=timezone.localdate() + timedelta(days=1),
#             include_breakfast=True,
#         )

#         # 3️⃣ Add dummy QR code file
#         self.voucher.qr_code_image.save(
#             f'test_qr_{self.voucher.id}.png',
#             ContentFile(b'Test QR content'),
#             save=True
#         )
#         self.voucher.save()

#     # ---------------- Create Voucher ----------------
#     def test_create_voucher_checkin(self):
#         url = reverse("checkin_form")  # Corrected
#         data = {
#             "guest_name": "Alice",
#             "room_no": "102",
#             "adults": 2,
#             "kids": 0,
#             "quantity": 1,
#             "country_code": "+91",
#             "phone_number": "9876543211",
#             "email": "alice@example.com",
#             "check_in_date": timezone.localdate().isoformat(),
#             "check_out_date": (timezone.localdate() + timedelta(days=1)).isoformat(),
#             "include_breakfast": "on",
#         }
#         response = self.client.post(url, data)
#         self.assertEqual(response.status_code, 200)
#         self.assertTrue(Voucher.objects.filter(guest_name="Alice").exists())
#         voucher = Voucher.objects.get(guest_name="Alice")
#         self.assertIsNotNone(voucher.qr_code_image)
#         self.assertTrue(voucher.include_breakfast)

#     # ---------------- Voucher Landing Page ----------------
#     def test_voucher_landing_page(self):
#         url = reverse("voucher_landing", args=[self.voucher.voucher_code])
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, self.voucher.guest_name)

#     # ---------------- Scan & Validate Voucher ----------------
#     def test_validate_voucher_first_time(self):
#         url = reverse("validate_voucher")
#         response = self.client.get(url, {"code": self.voucher.voucher_code})
#         self.assertEqual(response.status_code, 200)
#         data = response.json()
#         self.assertTrue(data["success"])
#         self.assertTrue(data["redeemed"])
#         self.assertEqual(data["scan_count"], 1)

#     def test_validate_voucher_second_time(self):
#         url = reverse("validate_voucher")
#         self.client.get(url, {"code": self.voucher.voucher_code})
#         response = self.client.get(url, {"code": self.voucher.voucher_code})
#         data = response.json()
#         self.assertFalse(data["success"])
#         self.assertIn("already used", data["message"].lower())

#     # ---------------- Invalid Voucher ----------------
#     def test_validate_invalid_voucher(self):
#         url = reverse("validate_voucher")
#         response = self.client.get(url, {"code": "INVALID123"})
#         self.assertEqual(response.status_code, 404)
#         self.assertIn("invalid voucher code", response.json()["message"].lower())

#     # ---------------- Expired Voucher ----------------
#     def test_validate_expired_voucher(self):
#         self.voucher.check_out_date = timezone.localdate() - timedelta(days=1)
#         self.voucher.save()
#         url = reverse("validate_voucher")
#         response = self.client.get(url, {"code": self.voucher.voucher_code})
#         self.assertEqual(response.status_code, 400)
#         self.assertIn("expired", response.json()["message"].lower())

#     # ---------------- Mark Checkout ----------------
#     def test_mark_checkout(self):
#         url = reverse("checkout", args=[self.voucher.id])  # Corrected
#         response = self.client.post(url)
#         self.assertEqual(response.status_code, 200)
#         voucher = Voucher.objects.get(id=self.voucher.id)
#         self.assertEqual(voucher.check_out_date, timezone.localdate())

#     # ---------------- Breakfast Voucher Report Export ----------------
#     def test_breakfast_voucher_report_export(self):
#         url = reverse("breakfast_voucher_report") + "?export=1"
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(
#             response["Content-Type"],
#             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from datetime import date, timedelta

from hotel_app.models import (
    Building,
    Floor,
    Location,
    LocationFamily,
    LocationType,
    Voucher,
    GymMember
)


# -------------------------------
# BUILDING TESTS
# -------------------------------
class BuildingsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.building_data = {"name": "Test Building"}

    def test_create_building(self):
        response = self.client.post('/api/buildings/', self.building_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Building.objects.count(), 1)

    def test_list_buildings(self):
        Building.objects.create(**self.building_data)
        response = self.client.get('/api/buildings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


# -------------------------------
# FLOOR TESTS
# -------------------------------
class FloorsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.building = Building.objects.create(name="Test Building")
        self.valid_floor_data = {
            "floor_name": "Test Floor",
            "floor_number": 1,
            "building": self.building.building_id
        }

    def test_create_floor(self):
        response = self.client.post('/api/floors/', self.valid_floor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Floor.objects.count(), 1)

    def test_list_floors(self):
        Floor.objects.create(floor_name="F1", floor_number=1, building=self.building)
        response = self.client.get('/api/floors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


# -------------------------------
# LOCATION FAMILY TESTS
# -------------------------------
class LocationFamiliesAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.valid_family_data = {"name": "Guestroom"}

    def test_create_family(self):
        response = self.client.post('/api/location-families/', self.valid_family_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LocationFamily.objects.count(), 1)


# -------------------------------
# LOCATION TYPE TESTS
# -------------------------------
class TypesAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.family = LocationFamily.objects.create(name="Guestroom")
        self.valid_type_data = {"name": "Deluxe", "family": self.family.family_id}

    def test_create_type(self):
        response = self.client.post('/api/types/', self.valid_type_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LocationType.objects.count(), 1)


# -------------------------------
# LOCATION TESTS
# -------------------------------
class LocationsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.building = Building.objects.create(name="Test Building")
        self.floor = Floor.objects.create(floor_name="Test Floor", floor_number=1, building=self.building)
        self.family = LocationFamily.objects.create(name="Guestroom")
        self.type = LocationType.objects.create(name="Deluxe", family=self.family)
        self.valid_location_data = {
            "name": "Room 101",
            "room_no": "101",
            "family": self.family.family_id,
            "type": self.type.type_id,
            "floor": self.floor.floor_id,
            "building": self.building.building_id
        }

    def test_create_location(self):
        response = self.client.post('/api/locations/', self.valid_location_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Location.objects.count(), 1)


# -------------------------------
# VOUCHER TESTS
# -------------------------------
class VouchersAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.building = Building.objects.create(name="Test Building")
        self.floor = Floor.objects.create(floor_name="Test Floor", floor_number=1, building=self.building)
        self.family = LocationFamily.objects.create(name="Guestroom")
        self.type = LocationType.objects.create(name="Deluxe", family=self.family)
        self.location = Location.objects.create(
            name="Room 101",
            room_no="101",
            family=self.family,
            type=self.type,
            floor=self.floor,
            building=self.building
        )
        self.voucher_data = {
            "guest_name": "John Doe",
            "country_code": "+91",
            "phone_number": "9876543210",
            "room_no": "101",
            "check_in_date": str(date.today()),
            "check_out_date": str(date.today() + timedelta(days=2)),
            "adults": 2,
            "kids": 1,
            "include_breakfast": True
        }

    def test_create_voucher(self):
        response = self.client.post('/api/vouchers/', self.voucher_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Voucher.objects.count(), 1)

    def test_voucher_report(self):
        Voucher.objects.create(**self.voucher_data)
        response = self.client.get('/api/vouchers/report/')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])


# -------------------------------
# MEMBER TESTS
# -------------------------------
class MembersAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.valid_member_data = {
            "full_name": "John Doe",
            "nik": "1234567890",
            "address": "123 Main St",
            "city": "Anytown",
            "religion": "Christian",
            "gender": "Male",
            "occupation": "Engineer",
            "phone": "1234567890",
            "email": "john@example.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "customer_code": "MEM001"
        }

    def test_create_member(self):
        response = self.client.post('/api/members/', self.valid_member_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
        self.assertTrue(GymMember.objects.exists())

    def test_list_members(self):
        GymMember.objects.create(**{k: v for k, v in self.valid_member_data.items() if k != "confirm_password"})
        response = self.client.get('/api/members/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
