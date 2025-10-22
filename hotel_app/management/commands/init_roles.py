"""
Management command to initialize roles and permissions for the hotel management system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from hotel_app.models import (
    Department, Location, RequestType, Checklist,
    Complaint, BreakfastVoucher, Review, Guest,
    Voucher, VoucherScan, ServiceRequest, UserProfile,
    UserGroup, UserGroupMembership, Notification, GymMember,
    SLAConfiguration, DepartmentRequestSLA
)


class Command(BaseCommand):
    help = 'Initialize roles and permissions for the hotel management system'

    def handle(self, *args, **options):
        self.stdout.write(
            'Initializing roles and permissions...'
        )

        # Create or get groups
        admin_group, created = Group.objects.get_or_create(name='Admins')
        if created:
            self.stdout.write(f'Created Admins group')
        else:
            self.stdout.write(f'Found existing Admins group')

        staff_group, created = Group.objects.get_or_create(name='Staff')
        if created:
            self.stdout.write(f'Created Staff group')
        else:
            self.stdout.write(f'Found existing Staff group')

        user_group, created = Group.objects.get_or_create(name='Users')
        if created:
            self.stdout.write(f'Created Users group')
        else:
            self.stdout.write(f'Found existing Users group')

        # Assign permissions to Admins group (full access)
        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)
        self.stdout.write(
            f'Assigned {admin_permissions.count()} permissions to Admins group'
        )

        # Assign permissions to Staff group (operational access)
        staff_permissions = []
        
        # Get content types for models staff should have access to
        models_for_staff = [
            ServiceRequest, Voucher, GymMember, Review, 
            Department, Location, RequestType
        ]
        
        for model in models_for_staff:
            ct = ContentType.objects.get_for_model(model)
            # Add view, add, change permissions (exclude delete for most)
            perms = Permission.objects.filter(
                content_type=ct,
                codename__in=[
                    f'view_{model._meta.model_name}',
                    f'add_{model._meta.model_name}',
                    f'change_{model._meta.model_name}'
                ]
            )
            staff_permissions.extend(perms)
        
        # Add some specific permissions for staff
        additional_perms = [
            'view_userprofile',
            'change_userprofile',
        ]
        
        for perm_codename in additional_perms:
            try:
                perm = Permission.objects.get(codename=perm_codename)
                staff_permissions.append(perm)
            except Exception:
                self.stdout.write(
                    f'Permission {perm_codename} not found'
                )
        
        staff_group.permissions.set(staff_permissions)
        self.stdout.write(
            f'Assigned {len(staff_permissions)} permissions to Staff group'
        )

        # Assign permissions to Users group (limited access)
        user_permissions = []
        
        # Users can view and add service requests (tickets)
        service_request_ct = ContentType.objects.get_for_model(ServiceRequest)
        user_permissions.extend(
            Permission.objects.filter(
                content_type=service_request_ct,
                codename__in=['view_servicerequest', 'add_servicerequest']
            )
        )
        
        # Users can view and add reviews
        review_ct = ContentType.objects.get_for_model(Review)
        user_permissions.extend(
            Permission.objects.filter(
                content_type=review_ct,
                codename__in=['view_review', 'add_review']
            )
        )
        
        # Users can view their own profile
        userprofile_ct = ContentType.objects.get_for_model(UserProfile)
        user_permissions.extend(
            Permission.objects.filter(
                content_type=userprofile_ct,
                codename__in=['view_userprofile', 'change_userprofile']
            )
        )
        
        user_group.permissions.set(user_permissions)
        self.stdout.write(
            f'Assigned {len(user_permissions)} permissions to Users group'
        )

        self.stdout.write(
            'Role and permission initialization completed successfully!'
        )