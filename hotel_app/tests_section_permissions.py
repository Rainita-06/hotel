"""
Unit tests for section-based permissions system.

Tests cover:
- Permission creation
- Permission checking
- UserProfile ↔ Group syncing
- View decorators and mixins
- Template tags
- API endpoints
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from hotel_app.models import UserProfile, Section
from hotel_app.section_permissions import (
    user_has_section_permission,
    require_section_permission,
    SectionPermissionRequiredMixin,
)
from hotel_app.signals import ROLE_TO_GROUP_MAPPING
import json


class SectionPermissionsTestCase(TestCase):
    """Test section permission creation and checking."""
    
    def setUp(self):
        """Set up test data."""
        # Create sections
        self.sections = Section.get_or_create_sections()
        
        # Create users
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@test.com',
            password='testpass123',
            is_superuser=True
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        
        # Create groups
        self.admin_group = Group.objects.create(name='Admins')
        self.staff_group = Group.objects.create(name='Staff')
        self.user_group = Group.objects.create(name='Users')
        
        # Create permissions for sections
        section_content_type = ContentType.objects.get_for_model(Section)
        
        for section in self.sections:
            for action in ['view', 'add', 'change', 'delete']:
                codename = section.get_permission_codename(action)
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=section_content_type,
                    defaults={'name': f'Can {action} {section.display_name}'}
                )
        
        # Assign users to groups
        self.admin_user.groups.add(self.admin_group)
        self.staff_user.groups.add(self.staff_group)
        self.regular_user.groups.add(self.user_group)
        
        # Assign permissions to groups
        # Admin group gets all permissions for users section
        users_section = Section.objects.get(name='users')
        for action in ['view', 'add', 'change', 'delete']:
            codename = users_section.get_permission_codename(action)
            permission = Permission.objects.get(
                codename=codename,
                content_type=section_content_type
            )
            self.admin_group.permissions.add(permission)
        
        # Staff group gets view and change for users section
        for action in ['view', 'change']:
            codename = users_section.get_permission_codename(action)
            permission = Permission.objects.get(
                codename=codename,
                content_type=section_content_type
            )
            self.staff_group.permissions.add(permission)
        
        # User group gets only view for users section
        view_permission = Permission.objects.get(
            codename=users_section.get_permission_codename('view'),
            content_type=section_content_type
        )
        self.user_group.permissions.add(view_permission)
    
    def test_section_creation(self):
        """Test that sections are created correctly."""
        self.assertEqual(Section.objects.count(), len(self.sections))
        
        users_section = Section.objects.get(name='users')
        self.assertEqual(users_section.display_name, 'Users')
        self.assertTrue(users_section.is_active)
    
    def test_permission_creation(self):
        """Test that permissions are created for sections."""
        section_content_type = ContentType.objects.get_for_model(Section)
        users_section = Section.objects.get(name='users')
        
        for action in ['view', 'add', 'change', 'delete']:
            codename = users_section.get_permission_codename(action)
            permission = Permission.objects.get(
                codename=codename,
                content_type=section_content_type
            )
            self.assertIsNotNone(permission)
            self.assertEqual(permission.codename, codename)
    
    def test_superuser_has_all_permissions(self):
        """Test that superuser has all permissions."""
        for section in self.sections:
            for action in ['view', 'add', 'change', 'delete']:
                self.assertTrue(
                    user_has_section_permission(self.superuser, section.name, action),
                    f"Superuser should have {action} permission for {section.name}"
                )
    
    def test_admin_user_permissions(self):
        """Test admin user permissions."""
        # Admin should have all permissions for users section
        self.assertTrue(user_has_section_permission(self.admin_user, 'users', 'view'))
        self.assertTrue(user_has_section_permission(self.admin_user, 'users', 'add'))
        self.assertTrue(user_has_section_permission(self.admin_user, 'users', 'change'))
        self.assertTrue(user_has_section_permission(self.admin_user, 'users', 'delete'))
        
        # Admin should not have permissions for other sections (unless assigned)
        self.assertFalse(user_has_section_permission(self.admin_user, 'locations', 'view'))
    
    def test_staff_user_permissions(self):
        """Test staff user permissions."""
        # Staff should have view and change permissions for users section
        self.assertTrue(user_has_section_permission(self.staff_user, 'users', 'view'))
        self.assertFalse(user_has_section_permission(self.staff_user, 'users', 'add'))
        self.assertTrue(user_has_section_permission(self.staff_user, 'users', 'change'))
        self.assertFalse(user_has_section_permission(self.staff_user, 'users', 'delete'))
    
    def test_regular_user_permissions(self):
        """Test regular user permissions."""
        # Regular user should have only view permission for users section
        self.assertTrue(user_has_section_permission(self.regular_user, 'users', 'view'))
        self.assertFalse(user_has_section_permission(self.regular_user, 'users', 'add'))
        self.assertFalse(user_has_section_permission(self.regular_user, 'users', 'change'))
        self.assertFalse(user_has_section_permission(self.regular_user, 'users', 'delete'))
    
    def test_userprofile_group_sync(self):
        """Test that UserProfile role syncs with Group membership."""
        # Create UserProfile for admin user
        profile = UserProfile.objects.create(
            user=self.admin_user,
            full_name='Admin User',
            role='admin'
        )
        
        # Check that user is in Admins group
        self.assertTrue(self.admin_user.groups.filter(name='Admins').exists())
        
        # Change role to staff
        profile.role = 'staff'
        profile.save()
        
        # Check that user is now in Staff group (and not in Admins)
        self.assertTrue(self.admin_user.groups.filter(name='Staff').exists())
        self.assertFalse(self.admin_user.groups.filter(name='Admins').exists())
    
    def test_group_to_userprofile_sync(self):
        """Test that Group membership syncs back to UserProfile role."""
        # Create UserProfile for staff user
        profile = UserProfile.objects.create(
            user=self.staff_user,
            full_name='Staff User',
            role='user'
        )
        
        # Add user to Admins group
        self.staff_user.groups.add(self.admin_group)
        
        # Check that profile role is updated to admin
        profile.refresh_from_db()
        self.assertEqual(profile.role, 'admin')
    
    def test_api_group_permissions(self):
        """Test API endpoint for getting group permissions."""
        client = Client()
        client.login(username='admin', password='testpass123')
        
        url = reverse('dashboard:api_group_permissions', args=[self.admin_group.id])
        response = client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('permissions', data)
        self.assertIn('permissions_by_section', data)
        self.assertIn('users', data['permissions_by_section'])
        self.assertTrue(data['permissions_by_section']['users']['view'])
        self.assertTrue(data['permissions_by_section']['users']['add'])
    
    def test_api_group_permissions_update(self):
        """Test API endpoint for updating group permissions."""
        client = Client()
        client.login(username='admin', password='testpass123')
        
        url = reverse('dashboard:api_group_permissions_update', args=[self.staff_group.id])
        
        # Update permissions to include add permission
        data = {
            'permissions_by_section': {
                'users': {
                    'view': True,
                    'add': True,
                    'change': True,
                    'delete': False
                }
            }
        }
        
        response = client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # Check that permissions were updated
        self.staff_group.refresh_from_db()
        section_content_type = ContentType.objects.get_for_model(Section)
        users_section = Section.objects.get(name='users')
        
        add_permission = Permission.objects.get(
            codename=users_section.get_permission_codename('add'),
            content_type=section_content_type
        )
        
        self.assertTrue(self.staff_group.permissions.filter(id=add_permission.id).exists())
    
    def test_manage_users_profiles_view(self):
        """Test that manage_users_profiles view requires permission."""
        client = Client()
        
        # Test without login
        url = reverse('dashboard:manage_users_profiles')
        response = client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with user without permission
        client.login(username='user', password='testpass123')
        response = client.get(url)
        # Should either redirect or show permission denied
        self.assertIn(response.status_code, [302, 403])
        
        # Test with user with permission
        client.logout()
        client.login(username='admin', password='testpass123')
        response = client.get(url)
        self.assertEqual(response.status_code, 200)


class SectionPermissionDecoratorsTestCase(TestCase):
    """Test section permission decorators and mixins."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create sections and permissions
        Section.get_or_create_sections()
        section_content_type = ContentType.objects.get_for_model(Section)
        users_section = Section.objects.get(name='users')
        
        view_permission = Permission.objects.create(
            codename=users_section.get_permission_codename('view'),
            content_type=section_content_type,
            name='Can view users'
        )
        
        group = Group.objects.create(name='TestGroup')
        group.permissions.add(view_permission)
        self.user.groups.add(group)
    
    def test_user_has_section_permission_function(self):
        """Test user_has_section_permission function."""
        self.assertTrue(user_has_section_permission(self.user, 'users', 'view'))
        self.assertFalse(user_has_section_permission(self.user, 'users', 'add'))
        self.assertFalse(user_has_section_permission(self.user, 'users', 'change'))
        self.assertFalse(user_has_section_permission(self.user, 'users', 'delete'))


class TemplateTagsTestCase(TestCase):
    """Test template tags for section permissions."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create sections and permissions
        Section.get_or_create_sections()
        section_content_type = ContentType.objects.get_for_model(Section)
        users_section = Section.objects.get(name='users')
        
        view_permission = Permission.objects.create(
            codename=users_section.get_permission_codename('view'),
            content_type=section_content_type,
            name='Can view users'
        )
        
        group = Group.objects.create(name='TestGroup')
        group.permissions.add(view_permission)
        self.user.groups.add(group)
    
    def test_has_section_permission_filter(self):
        """Test has_section_permission template filter."""
        from hotel_app.templatetags.section_permissions import has_section_permission
        
        self.assertTrue(has_section_permission(self.user, 'users.view'))
        self.assertFalse(has_section_permission(self.user, 'users.add'))
        self.assertFalse(has_section_permission(None, 'users.view'))
        
        # Test with unauthenticated user
        anonymous_user = User()
        anonymous_user.is_authenticated = False
        self.assertFalse(has_section_permission(anonymous_user, 'users.view'))

