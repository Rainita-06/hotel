


# from enum import member
# from typing import Type
# from django.test import TestCase
# from django.urls import reverse
# from rest_framework.test import APIClient
# from rest_framework import status
# from datetime import date, timedelta
# from hotel_app.models import Building, Floor, Location, LocationFamily, LocationType, Voucher

# class VoucherAPITests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.voucher_data = {
#             "guest_name": "John Doe",
#             "room_no": "101",
#             "phone_number": "9876543210",
#             "country_code": "+91",
#             "adults": 2,
#             "kids": 1,
#             "check_in_date": date.today(),
#             "check_out_date": date.today() + timedelta(days=2),
#             "include_breakfast": True
#         }

#     def test_create_voucher(self):
#         """✅ Should create a voucher and auto-generate QR"""
#         response = self.client.post("/api/vouchers/", self.voucher_data, format="json")
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertTrue(Voucher.objects.exists())
#         voucher = Voucher.objects.first()
#         self.assertIsNotNone(voucher.qr_code_image)
#         self.assertIsNotNone(voucher.voucher_code)

#     def test_validate_voucher(self):
#         """✅ Should validate a voucher successfully"""
#         voucher = Voucher.objects.create(**self.voucher_data)
#         voucher.voucher_code = "ABC123"
#         voucher.save()

#         response = self.client.get(f"/api/vouchers/validate/?code={voucher.voucher_code}")
#         self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

#     def test_report(self):
#         """✅ Should return report counts"""
#         Voucher.objects.create(**self.voucher_data)
#         response = self.client.get("/api/vouchers/report/")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("daily_checkins", response.data)

#     def test_checkout(self):
#         """✅ Should mark checkout date for voucher"""
#         voucher = Voucher.objects.create(**self.voucher_data)
#         url = f"/api/vouchers/{voucher.id}/checkout/"
#         response = self.client.post(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         voucher.refresh_from_db()
#         self.assertEqual(voucher.check_out_date, date.today())

#     def test_share_whatsapp(self):
#         """✅ Should return WhatsApp share URL"""
#         voucher = Voucher.objects.create(**self.voucher_data)
#         url = f"/api/vouchers/{voucher.id}/share/"
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("whatsapp_url", response.data)


from django.test import TestCase
from django.urls import reverse
from hotel_app.hotel_app.models import Building, Floor, Location, LocationFamily, LocationType
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
import json

class FloorsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=User.objects.create_user('testuser', password='testpass'))
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.valid_floor_data = {
            "floor_name": "Test Floor",
            "floor_number": 1,
            "building": 1
        }
        self.building = Building.objects.create(name="Test Building")

    def test_create_floor(self):
        response = self.client.post('/api/floors/', self.valid_floor_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Floor.objects.count(), 1)

    def test_list_floors(self):
        Floor.objects.create(**self.valid_floor_data)
        response = self.client.get('/api/floors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_floor(self):
        floor = Floor.objects.create(**self.valid_floor_data)
        updated_data = {"floor_name": "Updated Floor", "floor_number": 1, "building": 1}
        response = self.client.put(f'/api/floors/{floor.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        floor.refresh_from_db()
        self.assertEqual(floor.floor_name, "Updated Floor")

    def test_delete_floor(self):
        floor = Floor.objects.create(**self.valid_floor_data)
        response = self.client.delete(f'/api/floors/{floor.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Floor.objects.count(), 0)

    def test_search_floors(self):
        Floor.objects.create(**self.valid_floor_data)
        response = self.client.get('/api/floors/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class BuildingsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=User.objects.create_user('testuser', password='testpass'))
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.valid_building_data = {"name": "Test Building"}

    def test_create_building(self):
        response = self.client.post('/api/buildings/', self.valid_building_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Building.objects.count(), 1)

    def test_list_buildings(self):
        Building.objects.create(**self.valid_building_data)
        response = self.client.get('/api/buildings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_building(self):
        building = Building.objects.create(**self.valid_building_data)
        updated_data = {"name": "Updated Building"}
        response = self.client.put(f'/api/buildings/{building.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        building.refresh_from_db()
        self.assertEqual(building.name, "Updated Building")

    def test_delete_building(self):
        building = Building.objects.create(**self.valid_building_data)
        response = self.client.delete(f'/api/buildings/{building.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Building.objects.count(), 0)

    def test_search_buildings(self):
        Building.objects.create(**self.valid_building_data)
        response = self.client.get('/api/buildings/?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class LocationFamiliesAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=User.objects.create_user('testuser', password='testpass'))
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.valid_family_data = {"name": "Guestroom"}

    def test_create_family(self):
        response = self.client.post('/api/location-families/', self.valid_family_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LocationFamily.objects.count(), 1)

    def test_list_families(self):
        LocationFamily.objects.create(**self.valid_family_data)
        response = self.client.get('/api/location-families/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_family(self):
        family = LocationFamily.objects.create(**self.valid_family_data)
        updated_data = {"name": "Guestroom Updated"}
        response = self.client.put(f'/api/location-families/{family.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        family.refresh_from_db()
        self.assertEqual(family.name, "Guestroom Updated")

    def test_delete_family(self):
        family = LocationFamily.objects.create(**self.valid_family_data)
        response = self.client.delete(f'/api/location-families/{family.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(LocationFamily.objects.count(), 0)

    def test_search_families(self):
        LocationFamily.objects.create(**self.valid_family_data)
        response = self.client.get('/api/location-families/?search=Guest')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class TypesAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=User.objects.create_user('testuser', password='testpass'))
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.family = LocationFamily.objects.create(name="Guestroom")
        self.valid_type_data = {"name": "Deluxe", "family": self.family.id}

    def test_create_type(self):
        response = self.client.post('/api/types/', self.valid_type_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LocationType.objects.count(), 1)

    def test_list_types(self):
        LocationType.objects.create(**self.valid_type_data)
        response = self.client.get('/api/types/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_type(self):
        type_obj = LocationType.objects.create(**self.valid_type_data)
        updated_data = {"name": "Deluxe Updated", "family": self.family.id}
        response = self.client.put(f'/api/types/{type_obj.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        type_obj.refresh_from_db()
        self.assertEqual(type_obj.name, "Deluxe Updated")

    def test_delete_type(self):
        type_obj = LocationType.objects.create(**self.valid_type_data)
        response = self.client.delete(f'/api/types/{type_obj.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(LocationType.objects.count(), 0)

    def test_search_types(self):
        LocationType.objects.create(**self.valid_type_data)
        response = self.client.get('/api/types/?search=Deluxe')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class LocationsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=User.objects.create_user('testuser', password='testpass'))
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        self.building = Building.objects.create(name="Test Building")
        self.floor = Floor.objects.create(floor_name="Test Floor", floor_number=1, building=self.building)
        self.family = LocationFamily.objects.create(name="Guestroom")
        self.type = LocationType.objects.create(name="Deluxe", family=self.family)
        self.valid_location_data = {
            "name": "Room 101",
            "room_no": "101",
            "family": self.family.id,
            "type": self.type.id,
            "floor": self.floor.id,
            "building": self.building.id
        }

    def test_create_location(self):
        response = self.client.post('/api/locations/', self.valid_location_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Location.objects.count(), 1)

    def test_list_locations(self):
        Location.objects.create(**self.valid_location_data)
        response = self.client.get('/api/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_location(self):
        location = Location.objects.create(**self.valid_location_data)
        updated_data = self.valid_location_data.copy()
        updated_data["name"] = "Room 102"
        response = self.client.put(f'/api/locations/{location.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        location.refresh_from_db()
        self.assertEqual(location.name, "Room 102")

    def test_delete_location(self):
        location = Location.objects.create(**self.valid_location_data)
        response = self.client.delete(f'/api/locations/{location.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Location.objects.count(), 0)

    def test_search_locations(self):
        Location.objects.create(**self.valid_location_data)
        response = self.client.get('/api/locations/?search=Room 101')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

class VouchersAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=User.objects.create_user('testuser', password='testpass'))
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
        self.valid_voucher_data = {
            "guest_name": "John Doe",
            "country_code": "+1",
            "phone_number": "1234567890",
            "room_no": "101",
            "check_in_date": "2023-01-01",
            "check_out_date": "2023-01-02",
            "adults": 1,
            "kids": 0,
            "include_breakfast": True
        }
        self.voucher = Voucher.objects.create(**self.valid_voucher_data)

    def test_create_voucher(self):
        response = self.client.post('/api/vouchers/', self.valid_voucher_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Voucher.objects.count(), 2)  # Including existing one

    def test_list_vouchers(self):
        response = self.client.get('/api/vouchers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_voucher(self):
        updated_data = self.valid_voucher_data.copy()
        updated_data["guest_name"] = "Jane Doe"
        response = self.client.put(f'/api/vouchers/{self.voucher.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.guest_name, "Jane Doe")

    def test_delete_voucher(self):
        response = self.client.delete(f'/api/vouchers/{self.voucher.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Voucher.objects.count(), 0)

    def test_share_voucher(self):
        response = self.client.get(f'/api/vouchers/{self.voucher.id}/share/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validate_voucher(self):
        response = self.client.get('/api/vouchers/validate/?code=BFX12345')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_voucher_report(self):
        response = self.client.get('/api/vouchers/report/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_voucher_checkout(self):
        response = self.client.post(f'/api/vouchers/{self.voucher.id}/checkout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class MembersAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = Token.objects.create(user=User.objects.create_user('testuser', password='testpass'))
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
        self.member = member.objects.create(**self.valid_member_data)

    def test_create_member(self):
        response = self.client.post('/api/members/', self.valid_member_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(member.objects.count(), 2)  # Including existing one

    def test_list_members(self):
        response = self.client.get('/api/members/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_member(self):
        updated_data = self.valid_member_data.copy()
        updated_data["full_name"] = "John Smith"
        response = self.client.put(f'/api/members/{self.member.id}/', updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.refresh_from_db()
        self.assertEqual(self.member.full_name, "John Smith")

    def test_delete_member(self):
        response = self.client.delete(f'/api/members/{self.member.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(member.objects.count(), 0)

    def test_validate_member(self):
        response = self.client.get('/api/members/validate/?code=MEM001')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_member_without_auth(self):
        self.client.credentials()  # Remove auth
        response = self.client.get('/api/members/validate/?code=MEM001')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)