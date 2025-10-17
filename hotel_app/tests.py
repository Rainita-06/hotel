from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from hotel_app.models import Guest, Voucher
from datetime import date, timedelta

class UserPermissionTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
        
        # Create groups
        self.admins_group = Group.objects.create(name='Admins')
        self.staff_group = Group.objects.create(name='Staff')
        self.users_group = Group.objects.create(name='Users')
        
        # Assign users to groups
        self.admin_user.groups.add(self.admins_group)
        self.staff_user.groups.add(self.staff_group)
        self.regular_user.groups.add(self.users_group)
        
        # Create test data
        self.guest = Guest.objects.create(
            full_name='Test Guest',
            room_number='101',
            checkin_date=date.today(),
            checkout_date=date.today() + timedelta(days=2),
            breakfast_included=True
        )
        
        self.voucher = Voucher.objects.create(
            guest_name='Test Guest',
            room_number='101',
            check_in_date=date.today(),
            check_out_date=date.today() + timedelta(days=2),
            valid_dates=[str(date.today() + timedelta(days=1))]
        )
        
        # Create test client
        self.client = Client()

    def test_admin_access_to_admin_pages(self):
        """Test that admin users can access admin-only pages"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:users'))
        self.assertEqual(response.status_code, 200)

    def test_staff_access_to_staff_pages(self):
        """Test that staff users can access staff pages"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard:guests'))
        self.assertEqual(response.status_code, 200)

    def test_regular_user_access_restricted(self):
        """Test that regular users cannot access restricted pages"""
        self.client.login(username='user', password='testpass123')
        response = self.client.get(reverse('dashboard:users'))
        # Should be redirected or get permission denied
        self.assertIn(response.status_code, [302, 403])

    def test_staff_cannot_access_admin_pages(self):
        """Test that staff users cannot access admin-only pages"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('dashboard:users'))
        # Should be redirected or get permission denied
        self.assertIn(response.status_code, [302, 403])

    def test_template_tags(self):
        """Test custom template tags"""
        from hotel_app.templatetags.group_filters import has_group, is_admin, is_staff, has_permission
        
        # Test has_group
        self.assertTrue(has_group(self.admin_user, 'Admins'))
        self.assertFalse(has_group(self.staff_user, 'Admins'))
        
        # Test is_admin
        self.assertTrue(is_admin(self.admin_user))
        self.assertFalse(is_admin(self.staff_user))
        
        # Test is_staff
        self.assertTrue(is_staff(self.admin_user))
        self.assertTrue(is_staff(self.staff_user))
        self.assertFalse(is_staff(self.regular_user))
        
        # Test has_permission
        self.assertTrue(has_permission(self.admin_user, 'Admins'))
        self.assertTrue(has_permission(self.staff_user, ['Admins', 'Staff']))
        self.assertFalse(has_permission(self.regular_user, 'Admins'))

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, datetime, timedelta
from unittest.mock import patch
from hotel_app.models import Voucher, Guest

User = get_user_model()


class HotelAPITests(APITestCase):
    """
    Full CRUD tests for all endpoints defined in hotel_app/urls_api.py
    """

    def setUp(self):
        # Create a test user & authenticate
        self.user = User.objects.create_user(
            username="testuser", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    # ===========================
    # 1. Authentication
    # ===========================
    def test_login(self):
        url = reverse("token_obtain_pair")
        response = self.client.post(
            url, {"username": "testuser", "password": "password123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    # ===========================
    # 2. Users
    # ===========================
    def test_user_crud(self):
        # Create
        response = self.client.post(
            "/api/users/", {"username": "newuser", "password": "testpass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_id = response.data["id"]

        # Read
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/users/{user_id}/", {"username": "updateduser"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/users/{user_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 3. Departments
    # ===========================
    def test_department_crud(self):
        # Create
        response = self.client.post("/api/departments/", {"name": "Housekeeping"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        dept_id = response.data["id"]

        # Read
        response = self.client.get("/api/departments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/departments/{dept_id}/", {"name": "Reception"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/departments/{dept_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 4. User Groups
    # ===========================
    def test_user_group_crud(self):
        # Create
        response = self.client.post("/api/user-groups/", {"name": "Admins"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group_id = response.data["id"]

        # Read
        response = self.client.get("/api/user-groups/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/user-groups/{group_id}/", {"name": "Employees"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/user-groups/{group_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 5. Locations
    # ===========================
    def test_location_crud(self):
        # Create
        response = self.client.post("/api/locations/", {"name": "Lobby"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        loc_id = response.data["id"]

        # Read
        response = self.client.get("/api/locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/locations/{loc_id}/", {"name": "Main Lobby"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/locations/{loc_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 6. Complaints
    # ===========================
    def test_complaint_crud(self):
        # Create
        response = self.client.post("/api/complaints/", {"title": "AC not working"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        complaint_id = response.data["id"]

        # Read
        response = self.client.get("/api/complaints/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/complaints/{complaint_id}/", {"status": "Resolved"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/complaints/{complaint_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 7. Vouchers
    # ===========================
    def test_voucher_crud(self):
        # Create
        response = self.client.post("/api/vouchers/", {"guest": self.user.id,"valid_until": "2025-12-31"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        voucher_id = response.data["id"]

        # Read
        response = self.client.get("/api/vouchers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/vouchers/{voucher_id}/", {"redeemed": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/vouchers/{voucher_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 8. Reviews
    # ===========================
    def test_review_crud(self):
        # Create
        response = self.client.post("/api/reviews/", {"comment": "Great stay!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review_id = response.data["id"]

        # Read
        response = self.client.get("/api/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update
        response = self.client.patch(f"/api/reviews/{review_id}/", {"rating": 4}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Delete
        response = self.client.delete(f"/api/reviews/{review_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ===========================
    # 9. Dashboards (GET only)
    # ===========================
    def test_dashboard_overview(self):
        response = self.client.get(reverse("dashboard-overview"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_complaints(self):
        response = self.client.get(reverse("dashboard-complaints"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_reviews(self):
        response = self.client.get(reverse("dashboard-reviews"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ===========================
    # 10. Multi-day Voucher Scanning Test Case
    # ===========================
    def test_multi_day_voucher_scanning_scenario(self):
        """Test the exact scenario from requirements:
        Check-in: 6 September at 11:30 AM
        Check-out: 8 September at 10:30 AM
        Voucher Validity: 7 September (Day 1), 8 September (Day 2)
        Rule: Guest can scan voucher once per day, expires after check-out
        """
        # Setup: Create guest with specific dates
        guest = Guest.objects.create(
            full_name="Test Guest",
            room_number="101",
            phone_number="+1234567890",
            email="test@example.com",
            check_in_date=date(2024, 9, 6),
            check_out_date=date(2024, 9, 8)
        )
        
        # Create voucher with multi-day validity
        voucher = Voucher.objects.create(
            guest=guest,
            guest_name="Test Guest",
            room_number="101",
            check_in_date=date(2024, 9, 6),
            check_out_date=date(2024, 9, 8),
            valid_dates=["2024-09-07", "2024-09-08"],  # Day 1 and Day 2 breakfast
            voucher_type='breakfast',
            status='active'
        )
        
        # Day 1 (Sept 7): First scan - should SUCCEED
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(datetime(2024, 9, 7, 11, 30))
            response = self.client.post('/api/vouchers/validate/', {
                'voucher_code': voucher.voucher_code
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['valid'])
            self.assertEqual(response.data['scan_result'], 'success')
        
        # Refresh voucher to see updated scan_history
        voucher.refresh_from_db()
        self.assertIn("2024-09-07", voucher.scan_history)
        
        # Day 1 (Sept 7): Second scan attempt - should FAIL (already used)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(datetime(2024, 9, 7, 15, 0))
            response = self.client.post('/api/vouchers/validate/', {
                'voucher_code': voucher.voucher_code
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(response.data['valid'])
            self.assertEqual(response.data['scan_result'], 'already_redeemed')
            self.assertEqual(response.data['error_code'], 'ALREADY_USED')
        
        # Day 2 (Sept 8): First scan - should SUCCEED
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(datetime(2024, 9, 8, 8, 0))
            response = self.client.post('/api/vouchers/validate/', {
                'voucher_code': voucher.voucher_code
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['valid'])
            self.assertEqual(response.data['scan_result'], 'success')
        
        # Refresh voucher to see updated scan_history
        voucher.refresh_from_db()
        self.assertIn("2024-09-08", voucher.scan_history)
        self.assertTrue(voucher.redeemed)  # Should be fully redeemed now
        
        # Day 2 (Sept 8): Second scan attempt - should FAIL (already used)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(datetime(2024, 9, 8, 12, 0))
            response = self.client.post('/api/vouchers/validate/', {
                'voucher_code': voucher.voucher_code
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(response.data['valid'])
            self.assertEqual(response.data['scan_result'], 'already_redeemed')
            self.assertEqual(response.data['error_code'], 'ALREADY_USED')
        
        # Day 3 (Sept 9): After checkout - should FAIL (expired)
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(datetime(2024, 9, 9, 9, 0))
            response = self.client.post('/api/vouchers/validate/', {
                'voucher_code': voucher.voucher_code
            }, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(response.data['valid'])
            self.assertEqual(response.data['scan_result'], 'expired')
            self.assertEqual(response.data['error_code'], 'AFTER_CHECKOUT')
        
        # Verify scan history records
        scans = VoucherScan.objects.filter(voucher=voucher)
        self.assertEqual(scans.count(), 5)  # 2 successful + 3 failed attempts
        
        successful_scans = scans.filter(scan_result='success')
        self.assertEqual(successful_scans.count(), 2)
        
        failed_scans = scans.filter(scan_result__in=['already_redeemed', 'expired'])
        self.assertEqual(failed_scans.count(), 3)
