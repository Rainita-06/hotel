from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Import UserProfile inside the function to avoid circular import issues
        from .models import UserProfile
        # Use the model class directly instead of the imported one to avoid linter issues
        UserProfile._default_manager.create(user=instance, full_name=instance.get_full_name() or instance.username)


# Sync UserProfile role with Django Groups
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from .models import UserProfile

# Thread-local storage to prevent infinite loops
import threading
_sync_lock = threading.local()

def is_syncing():
    """Check if we're currently syncing to prevent infinite loops"""
    return getattr(_sync_lock, 'syncing', False)

def set_syncing(value):
    """Set sync flag to prevent infinite loops"""
    _sync_lock.syncing = value

@receiver(post_save, sender=UserProfile)
def sync_userprofile_to_group(sender, instance, created, **kwargs):
    """
    Sync UserProfile role with Django auth.Group membership.
    When a UserProfile's role changes, update the user's group membership.
    """
    # Prevent infinite loops
    if is_syncing():
        return
        
    try:
        set_syncing(True)
        user = instance.user
        role = (instance.role or '').strip()
        
        if not role:
            # Remove user from all groups if no role provided
            user.groups.clear()
            return
        
        # Get or create the group matching the profile role name
        group, _ = Group.objects.get_or_create(name=role)
        
        # Remove user from all groups first, then add the single role group
        user.groups.clear()
        user.groups.add(group)
            
    except Exception as e:
        # Don't break user creation if group sync fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error syncing UserProfile to Group: {str(e)}', exc_info=True)
    finally:
        set_syncing(False)


@receiver(m2m_changed, sender=User.groups.through)
def sync_user_groups_to_profile(sender, instance, action, pk_set, **kwargs):
    """
    Sync Django Group membership back to UserProfile role.
    When a user's group membership changes via m2m, update their UserProfile role.
    This handles cases where groups are changed directly (e.g., via admin).
    """
    # Only handle post_add and post_remove actions
    if action not in ['post_add', 'post_remove', 'post_clear']:
        return
        
    # Prevent infinite loops
    if is_syncing():
        return
        
    try:
        set_syncing(True)
        # Only sync if user has a profile
        if not hasattr(instance, 'userprofile'):
            return
        
        profile = instance.userprofile
        user = instance
        
        # Ensure user only belongs to a single group (primary role group)
        user_groups = list(user.groups.all())
        if user_groups:
            primary_group = user_groups[0]
            # Remove any additional groups beyond the first
            for extra_group in user_groups[1:]:
                user.groups.remove(extra_group)
            new_role = primary_group.name
        else:
            primary_group = None
            new_role = ''
        
        if profile.role != new_role:
            UserProfile.objects.filter(pk=profile.pk).update(role=new_role)
                
    except Exception as e:
        # Don't break user creation if profile sync fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error syncing User groups to UserProfile: {str(e)}', exc_info=True)
    finally:
        set_syncing(False)


# Audit logging for create/update/delete
from django.db.models.signals import post_delete, post_save
from django.apps import apps
from django.db.models.signals import pre_save
from django.utils import timezone
from django.conf import settings
from .whatsapp_service import whatsapp_service

# Get AuditLog model
AuditLog = apps.get_model('hotel_app', 'AuditLog')


def _log_action(actor, action, instance, changes=None):
    # Skip logging for AuditLog itself to prevent recursion
    if isinstance(instance, AuditLog):
        return
    try:
        AuditLog._default_manager.create(
            actor=actor if hasattr(actor, 'pk') else None,
            action=action,
            model_name=instance.__class__.__name__,
            object_pk=str(getattr(instance, 'pk', '')),
            changes=changes or {}
        )
    except Exception:
        # Avoid breaking requests if logging fails
        pass


def _get_current_user():
    """Get current user safely, handling missing django-currentuser"""
    try:
        # Use import_string to avoid linter issues
        get_current_authenticated_user = import_string('django_currentuser.middleware.get_current_authenticated_user')
        user = get_current_authenticated_user()()
        return user
    except (ImportError, Exception):
        # django-currentuser is not installed or other error
        return None


@receiver(post_save)
def model_saved(sender, instance, created, **kwargs):
    # Only log models from our app and exclude AuditLog to prevent recursion
    if sender._meta.app_label != 'hotel_app' or sender == AuditLog:
        return
    user = _get_current_user()
    _log_action(user, 'create' if created else 'update', instance)


@receiver(post_delete)
def model_deleted(sender, instance, **kwargs):
    # Only log models from our app and exclude AuditLog to prevent recursion
    if sender._meta.app_label != 'hotel_app' or sender == AuditLog:
        return
    user = _get_current_user()
    _log_action(user, 'delete', instance)


# -- Complaint specific signals for assignment, status changes and SLA tracking
Complaint = apps.get_model('hotel_app', 'Complaint')


@receiver(pre_save, sender=Complaint)
def complaint_pre_save(sender, instance, **kwargs):
    """Capture previous state before save."""
    try:
        if not instance.pk:
            instance._pre_save_instance = None
            return
        previous = Complaint._default_manager.filter(pk=instance.pk).first()
        instance._pre_save_instance = previous
    except Exception:
        instance._pre_save_instance = None


@receiver(post_save, sender=Complaint)
def complaint_post_save(sender, instance, created, **kwargs):
    """After complaint is saved, detect assignment and status changes and notify.

    Also update SLA breach flag if due_at passed and not resolved.
    """
    try:
        prev = getattr(instance, '_pre_save_instance', None)
        # Assignment changed
        if prev is None and instance.assigned_to:
            # new assignment
            msg = f"You have been assigned a complaint: {instance.subject}"
            # Try phone on assigned user profile
            phone = None
            try:
                profile = instance.assigned_to.userprofile
                phone = profile.phone
            except Exception:
                phone = None
            if phone:
                whatsapp_service.send_text(phone, msg)

        elif prev and prev.assigned_to != instance.assigned_to:
            # assignment changed
            if instance.assigned_to:
                msg = f"You have been assigned a complaint: {instance.subject}"
                phone = None
                try:
                    profile = instance.assigned_to.userprofile
                    phone = profile.phone
                except Exception:
                    phone = None
                if phone:
                    whatsapp_service.send_text(phone, msg)

        # Status change handling
        if prev is None and instance.status == 'in_progress':
            instance.started_at = timezone.now()
            instance.save()
        elif prev and prev.status != instance.status:
            # moved to in_progress
            if instance.status == 'in_progress' and not instance.started_at:
                instance.started_at = timezone.now()
                instance.save()
            # moved to resolved
            if instance.status == 'resolved' and not instance.resolved_at:
                instance.resolved_at = timezone.now()
                # compute sla breach
                if instance.due_at and instance.resolved_at > instance.due_at:
                    instance.sla_breached = True
                instance.save()

        # SLA breach check for unresolved complaints
        if not instance.resolved_at and instance.due_at and timezone.now() > instance.due_at:
            if not instance.sla_breached:
                instance.sla_breached = True
                instance.save()

    except Exception:
        # don't allow notification failures to interrupt request
        pass


# ---- Guest Check-in/Check-out WhatsApp Signals ----
from .models import Guest, ServiceRequest
from .whatsapp_workflow import workflow_handler


@receiver(pre_save, sender=Guest)
def guest_pre_save(sender, instance, **kwargs):
    """Capture previous state before save to detect check-in/check-out changes."""
    try:
        if not instance.pk:
            instance._pre_save_instance = None
            return
        previous = Guest.objects.filter(pk=instance.pk).first()
        instance._pre_save_instance = previous
    except Exception:
        instance._pre_save_instance = None


@receiver(post_save, sender=Guest)
def guest_post_save(sender, instance, created, **kwargs):
    """Send WhatsApp messages on check-in and check-out events."""
    try:
        prev = getattr(instance, '_pre_save_instance', None)
        
        # Check if check-in status changed
        if prev:
            prev_status = prev.get_current_status()
            current_status = instance.get_current_status()
            
            # Guest just checked in
            if prev_status != 'checked_in' and current_status == 'checked_in':
                workflow_handler.send_welcome_for_checkin(instance)
            
            # Guest just checked out
            if prev_status != 'checked_out' and current_status == 'checked_out':
                workflow_handler.send_checkout_feedback_invite(instance)
        elif created:
            # New guest - check if they're already checked in
            if instance.get_current_status() == 'checked_in':
                workflow_handler.send_welcome_for_checkin(instance)
    
    except Exception as e:
        # Don't allow notification failures to interrupt request
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error sending WhatsApp message for guest {instance.pk}: {str(e)}', exc_info=True)


@receiver(post_save, sender=ServiceRequest)
def service_request_post_save(sender, instance, created, **kwargs):
    """Send notifications when a service request is created or updated."""
    try:
        # Only send notifications for newly created requests
        if created:
            # For WhatsApp-created tickets, send notifications to department staff
            if instance.source == 'whatsapp':
                # Notify department staff
                instance.notify_department_staff()
                
                # Try to send WhatsApp acknowledgment to guest
                from hotel_app.dashboard_views import _send_ticket_acknowledgement
                _send_ticket_acknowledgement(instance, guest=instance.guest)
            else:
                # For non-WhatsApp tickets, notify department staff
                instance.notify_department_staff()
        else:
            # Handle status changes for existing requests
            prev_status = getattr(instance, '_pre_save_status', None)
            if prev_status and prev_status != instance.status:
                # Status has changed, send appropriate notifications
                if instance.status == 'accepted':
                    # Notify assigned user
                    instance.notify_assigned_user()
                elif instance.status == 'in_progress':
                    # Notify requester that work has started
                    if instance.requester_user:
                        from .utils import create_notification
                        create_notification(
                            recipient=instance.requester_user,
                            title=f"Work Started on Ticket #{instance.pk}",
                            message=f"Work has started on your ticket #{instance.pk}: {instance.request_type.name}.",
                            notification_type='info',
                            related_object=instance
                        )
                elif instance.status == 'completed':
                    # Notify requester that ticket is completed
                    if instance.requester_user:
                        from .utils import create_notification
                        create_notification(
                            recipient=instance.requester_user,
                            title=f"Ticket #{instance.pk} Completed",
                            message=f"Your ticket #{instance.pk} has been completed: {instance.request_type.name}.",
                            notification_type='success',
                            related_object=instance
                        )
                elif instance.status == 'closed':
                    # Notify requester that ticket is closed
                    instance.notify_requester_on_closure()
                elif instance.status == 'escalated':
                    # Notify department leader
                    instance.notify_department_leader_on_escalation()
                elif instance.status == 'rejected':
                    # Notify requester that ticket is rejected
                    if instance.requester_user:
                        from .utils import create_notification
                        create_notification(
                            recipient=instance.requester_user,
                            title=f"Ticket #{instance.pk} Rejected",
                            message=f"Your ticket #{instance.pk} has been rejected: {instance.request_type.name}.",
                            notification_type='warning',
                            related_object=instance
                        )
    except Exception as e:
        # Don't allow notification failures to interrupt request
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error sending notification for service request {instance.pk}: {str(e)}', exc_info=True)


@receiver(pre_save, sender=ServiceRequest)
def service_request_pre_save(sender, instance, **kwargs):
    """Capture previous state before save to detect status changes."""
    try:
        if not instance.pk:
            instance._pre_save_status = None
            return
        previous = ServiceRequest.objects.filter(pk=instance.pk).first()
        if previous:
            instance._pre_save_status = previous.status
        else:
            instance._pre_save_status = None
    except Exception:
        instance._pre_save_status = None

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import transaction
from .models import Building, Floor, LocationFamily, LocationType, Location
from django.core.files import File
from django.conf import settings
import os

# @receiver(post_migrate)
# def create_basic_location_data(sender, **kwargs):
#     if sender.name != "hotel_app":
#         return

#     print("🔥 Running basic location auto-setup...")

#     # ------------------------
#     # 1. BUILDING
#     # ------------------------
#     image_path = os.path.join(settings.MEDIA_ROOT, 'building_images/0911835b756e25e2aa10ac7329e7a6a3b6094cdb_1nJe526_NL7Ilw8.png')

#     with open(image_path, 'rb') as f:
#         main_bld, created = Building.objects.get_or_create(
#         name="Main Building",
#         defaults={
#             "description": "Primary building for hotel",
#             "image": File(f, name=os.path.basename(image_path))
#         }
#     )

#     if created:
#         print("Building created with default image")
#     else:
#         print("Building already exists")

#     # ------------------------
#     # 2. FIX FLOOR DUPLICATES
#     # ------------------------
#     def fix_floor_duplicates(building, floor_number):
#         floors = Floor.objects.filter(building=building, floor_number=floor_number)

#         if floors.count() > 1:
#             print(f"⚠ Removing duplicates for Floor {floor_number}")
#             # keep the first, delete the rest
#             floors.exclude(floor_id=floors.first().floor_id).delete()

#         # now safe to get_or_create
#         floor, _ = Floor.objects.get_or_create(
#             building=building,
#             floor_number=floor_number,
#             defaults={"floor_name": f"{floor_number} Floor"}
#         )
#         return floor

#     floor1 = fix_floor_duplicates(main_bld, 1)
#     floor2 = fix_floor_duplicates(main_bld, 2)

#     # ------------------------
#     # 3. LOCATION FAMILY
#     # ------------------------
#     guest_family, _ = LocationFamily.objects.get_or_create(name="Guest Room")
#     service_family, _ = LocationFamily.objects.get_or_create(name="Service Area")

#     # ------------------------
#     # 4. LOCATION TYPES
#     # ------------------------
#     deluxe, _ = LocationType.objects.get_or_create(name="Deluxe Room", family=guest_family)
#     lobby, _ = LocationType.objects.get_or_create(name="Lobby", family=service_family)

#     # ------------------------
#     # 5. LOCATIONS
#     # ------------------------
#     Location.objects.get_or_create(
#         name="Room 101",
#         room_no="101",
#         building=main_bld,
#         floor=floor2,
#         type=deluxe
#     )

#     Location.objects.get_or_create(
#         name="Main Lobby",
#         building=main_bld,
#         floor=floor1,
#         type=lobby
#     )

#     print("✅ Basic Location Data Setup Finished.")

# import os
# import requests
# from django.core.files.base import ContentFile
# from django.db.models.signals import post_migrate
# from django.dispatch import receiver

# @receiver(post_migrate)
# def create_basic_location_data(sender, **kwargs):
#     if sender.name != "hotel_app":
#         return

#     print("\n🔥 Auto-generating Base Location Set (6X Format)...\n")

#     # 1️⃣ Building details
#     building_names = [
#         ("Main Building", "Primary building"),
#         ("Royal Residency", "Luxury stay"),
#         ("Garden Block", "Nature view rooms"),
#         ("Sky Tower", "Top view suites"),
#         ("Heritage Wing", "Classic architecture"),
#         ("Elite Chamber", "VIP exclusive block"),
#     ]

#     # 2️⃣ CDN dummy images (these will be downloaded into ImageField)
#     cdn_images = [
#         "https://images.pexels.com/photos/261102/pexels-photo-261102.jpeg",
#     "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg",
#     "https://images.pexels.com/photos/164595/pexels-photo-164595.jpeg",
#     "https://images.pexels.com/photos/271619/pexels-photo-271619.jpeg",
#     "https://images.pexels.com/photos/323780/pexels-photo-323780.jpeg",
#     "https://images.pexels.com/photos/240112/pexels-photo-240112.jpeg"
#     ]

#     # 3️⃣ Buildings
#     buildings = []
#     for i, (name, desc) in enumerate(building_names):

#         building, created = Building.objects.get_or_create(
#             name=name,
#             defaults={"description": desc}
#         )

#         if created:
#             try:
#                 print(f"📡 Downloading image for {name} ...")

#                 response = requests.get(cdn_images[i])
#                 response.raise_for_status()

#                 image_name = f"{name.replace(' ', '_').lower()}.jpg"
#                 building.image.save(image_name, ContentFile(response.content), save=True)

#             except Exception as e:
#                 print(f"⚠ Image download failed for {name}: {e}")

#         print(f"🏢 {name} → {'CREATED' if created else 'Already Exists'}")
#         buildings.append(building)

#     print("✔ Buildings created with CDN images!")

#     # 🔥 Your remaining floors, families, types, locations logic continues here...


#     # =============================
#     # 2️⃣ Six Floors (1 per building)
#     # =============================
#     floors = []

#     for idx, b in enumerate(buildings, start=1):

#     # Remove duplicates cleanly
#         Floor.objects.filter(building=b, floor_number=idx).delete()

#     # Create fresh floor safely
#         floor = Floor.objects.create(
#         building=b,
#         floor_number=idx,
#         floor_name=f"Floor {idx}"
#     )

#         floors.append(floor)

#     print("🏢 Floors Created: 6 (Cleaned duplicates)")

#     # =============================
#     # 3️⃣ Six Location Families
#     # =============================
#     family_names = ["Guest Room","Service Area","Executive","Premium","Dining","General Utility"]
#     families=[LocationFamily.objects.get_or_create(name=n)[0] for n in family_names]
#     print("👨‍👩‍👦 Families created: 6")

#     # =============================
#     # 4️⃣ Six Location Types
#     # =============================
#     type_names = ["Deluxe Room","Suite Room","Lobby","Dining Hall","Executive Suite","Conference Hall"]
#     types=[LocationType.objects.get_or_create(name=t,family=families[i])[0] for i,t in enumerate(type_names)]
#     print("🏷 Types created: 6")

#     # =============================
#     # 5️⃣ Six Locations (One for each building)
#     # =============================
#     for i, b in enumerate(buildings):

#      Location.objects.get_or_create(
#         name=f"{101+i}",
        
#         building=b,
#         floor=floors[i],
#         type=types[i],
#         family=types[i].family,      # <<< 🔥 FAMILY FIXED HERE
#         defaults={}
#     )

#     print("📍 Locations Created: 6")

#     print("\n✔ SUCCESS → 6 Buildings | 6 Floors | 6 Families | 6 Types | 6 Locations Ready!\n")
import os
import requests
from django.core.files.base import ContentFile
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Building, Floor, LocationFamily, LocationType, Location

import os
import random
import requests
from django.core.files.base import ContentFile
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Building, Floor, LocationFamily, LocationType, Location


# -----------------------------------------------------
# GLOBAL HOTEL IMAGES (361×192)
# -----------------------------------------------------
BUILDING_IMAGE_URLS = [
    "https://images.pexels.com/photos/261146/pexels-photo-261146.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271689/pexels-photo-271689.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/3586960/pexels-photo-3586960.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261102/pexels-photo-261102.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/1643383/pexels-photo-1643383.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
]
TYPE_IMAGE_URLS = [
    "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261395/pexels-photo-261395.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/189296/pexels-photo-189296.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271639/pexels-photo-271639.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261411/pexels-photo-261411.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271618/pexels-photo-271618.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
]
# -----------------------------------------------------
# GLOBAL LOCATION FAMILY IMAGES (361×192)
# -----------------------------------------------------
FAMILY_IMAGE_URLS = [
    "https://images.pexels.com/photos/262048/pexels-photo-262048.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/262978/pexels-photo-262978.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/261395/pexels-photo-261395.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/189296/pexels-photo-189296.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271639/pexels-photo-271639.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
    "https://images.pexels.com/photos/271624/pexels-photo-271624.jpeg?auto=compress&cs=tinysrgb&w=361&h=192",
]
def assign_random_family_image(family_obj):
    try:
        url = random.choice(FAMILY_IMAGE_URLS)
        filename = url.split("/")[-1].split("?")[0]

        # Ensure folder exists: MEDIA_ROOT/location_families
        folder_path = os.path.join(settings.MEDIA_ROOT, "location_family")
        os.makedirs(folder_path, exist_ok=True)

        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            family_obj.image.save(
                f"location_families/{filename}",
                ContentFile(response.content),
                save=True
            )
            print(f"Auto-image assigned → Family: {family_obj.name}")
        else:
            print(f"Failed to download family image: {url}")

    except Exception as e:
        print(f"Family image assign error: {e}")


# -----------------------------------------------------
# FUNCTION → Assign random hotel image
# -----------------------------------------------------
from django.conf import settings

def assign_random_image(building_obj):
    try:
        url = random.choice(BUILDING_IMAGE_URLS)
        filename = url.split("/")[-1].split("?")[0]

        # Ensure folder exists: MEDIA_ROOT/building_images
        folder_path = os.path.join(settings.MEDIA_ROOT, "building_images")
        os.makedirs(folder_path, exist_ok=True)

        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:

            # Save inside building_images/
            building_obj.image.save(
                f"building_images/{filename}",   # <--- REQUIRED FOR CORRECT PATH
                ContentFile(response.content),
                save=True
            )

            print(f"Auto-image assigned → {building_obj.name}")
        else:
            print(f"Failed to download: {url}")

    except Exception as e:
        print(f"Image assign error: {e}")


def assign_random_type_image(type_obj):
    try:
        url = random.choice(TYPE_IMAGE_URLS)
        filename = url.split("/")[-1].split("?")[0]

        folder_path = os.path.join(settings.MEDIA_ROOT, "location_types")
        os.makedirs(folder_path, exist_ok=True)

        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            type_obj.image.save(
                f"type_images/{filename}",
                ContentFile(response.content),
                save=True
            )
            print(f"Auto-image assigned → {type_obj.name}")
    except Exception as e:
        print(f"Type image assign error: {e}")
# -----------------------------------------------------
# MAIN POST-MIGRATE SIGNAL
# -----------------------------------------------------
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_basic_location_data(sender, **kwargs):

    if sender.name != "hotel_app":
        return

    print("\n Auto-generating Base Location Set (6X Format)…\n")

    # -----------------------------------------------------
    # 1️⃣ BUILDINGS
    # -----------------------------------------------------
    building_names = [
        ("Main Building", "Primary building"),
        ("Royal Residency", "Luxury stay"),
        ("Garden Block", "Nature view rooms"),
        ("Sky Tower", "Top view suites"),
        ("Heritage Wing", "Classic architecture"),
        ("Elite Chamber", "VIP exclusive block"),
    ]

    buildings = []

    for name, desc in building_names:
        building, created = Building.objects.get_or_create(
            name=name,
            defaults={"description": desc}
        )

        print(f" {name} → {'CREATED' if created else 'Already Exists'}")

        if not building.image:
            assign_random_image(building)

        buildings.append(building)

    # -----------------------------------------------------
    # 2️⃣ FLOORS (SAFE + UNIQUE)
    # -----------------------------------------------------
    floors = []

    for idx, b in enumerate(buildings, start=1):
        floor, created = Floor.objects.get_or_create(
            building=b,
            floor_name=f"Floor {idx}",
            defaults={"floor_number": idx}
        )

        print(
            f" Floor {idx} ({b.name}) → {'CREATED' if created else 'Already Exists'}"
        )

        floors.append(floor)

    # -----------------------------------------------------
    # 3️⃣ FAMILIES
    # -----------------------------------------------------
    family_names = [
        "Guest Room",
        "Service Area",
        "Executive",
        "Premium",
        "Dining",
        "General Utility",
    ]

    families = []

    for name in family_names:
        family, created = LocationFamily.objects.get_or_create(name=name)

        print(f" {name} → {'CREATED' if created else 'Already Exists'}")

        if not family.image:
            assign_random_family_image(family)

        families.append(family)

    # -----------------------------------------------------
    # 4️⃣ TYPES (Family-bound UNIQUE)
    # -----------------------------------------------------
    type_names = [
        "Deluxe Room",
        "Suite Room",
        "Lobby",
        "Dining Hall",
        "Executive Suite",
        "Conference Hall",
    ]

    types = []

    for i, type_name in enumerate(type_names):
        type_obj, created = LocationType.objects.get_or_create(
            name=type_name,
            family=families[i]
        )

        print(
            f" {type_name} → {'CREATED' if created else 'Already Exists'}"
        )

        if not type_obj.image:
            assign_random_type_image(type_obj)

        types.append(type_obj)

    # -----------------------------------------------------
    # 5️⃣ LOCATIONS (FULLY SAFE)
    # -----------------------------------------------------
    for i, b in enumerate(buildings):
        location, created = Location.objects.get_or_create(
            name=str(101 + i),
            building=b,
            floor=floors[i],
            family=types[i].family,
            type=types[i]
        )

        print(
            f" Location {location.name} ({b.name}) → "
            f"{'CREATED' if created else 'Already Exists'}"
        )

    print(
        "\n SUCCESS → Buildings | Floors | Families | Types | Locations are READY "
        
    )
