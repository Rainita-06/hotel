import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import os
import random
import string

User = get_user_model()

# ---- Department & Groups ----

from django.contrib.auth.models import User
class Department(models.Model):
    department_id = models.BigAutoField(primary_key=True)
    # name = models.CharField(max_length=100,blank=False, null=False)   # updated (was 120)
    description = models.CharField(max_length=255, null=True, blank=True)  
    # lead = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)       # added
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='department_logos/', blank=True, null=True)

    class Meta:
        db_table = 'Department'
        
    def __str__(self):
        return str(self.name)

    @property
    def total_users(self):
        return User.objects.filter(department=self).count() 
        
    def get_logo_url(self):
        """Get the logo URL for this department, handling both old and new storage methods"""
        if self.logo:
            # Check if it's a new-style logo (stored in department directory)
            if self.logo.name and f'departments/{self.pk}/' in self.logo.name:
                return self.logo.url
            else:
                # Old-style logo, return as is
                return self.logo.url
        return None 

class Checklist(models.Model):
    checklist_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100,blank=False, null=False)
    location = models.ForeignKey('Location',blank=False, null=False, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'checklist'


class ChecklistItem(models.Model):
    item_id = models.BigAutoField(primary_key=True)
    checklist = models.ForeignKey('Checklist', models.DO_NOTHING,blank=False, null=False)
    label = models.CharField(max_length=240, blank=True, null=True)
    required = models.BooleanField(default=False)

    class Meta:
        db_table = 'checklist_item'

class UserGroup(models.Model):
    name = models.CharField(max_length=120, unique=True)

    # Added fields for richer metadata and association with departments
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_groups')

    def __str__(self):
        return str(self.name)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=15, blank=True, null=True)
    title = models.CharField(max_length=120, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True )
    avatar_url = models.URLField(blank=True, null=True)
    enabled = models.BooleanField(default=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    preferences = models.JSONField(blank=True, null=True)
    role = models.CharField(max_length=150, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.full_name or getattr(self.user, "username", "Unknown User"))
    
    def is_admin(self):
        role_value = (self.role or '').lower()
        if role_value in {'admin', 'admins', 'administrator', 'superuser'}:
            return True
        return self.user.is_superuser or self.user.groups.filter(name__iexact='Admins').exists()
    
    def is_staff_member(self):
        role_value = (self.role or '').lower()
        if role_value in {'staff', 'front desk', 'frontdesk', 'front desk team'}:
            return True
        return self.user.groups.filter(name__iexact='Staff').exists()
    
    def is_regular_user(self):
        role_value = (self.role or '').lower()
        if role_value in {'user', 'users'}:
            return True
        return self.user.groups.filter(name__iexact='Users').exists()
    


class UserGroupMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return str(f'{self.user} -> {self.group}')


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_pk = models.CharField(max_length=100, blank=True, null=True)
    changes = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(f"{self.action} {self.model_name} {self.object_pk} by {self.actor}")


# ---- Notification System ----

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('request', 'Service Request'),
        ('voucher', 'Voucher'),
        ('system', 'System'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    related_object_id = models.CharField(max_length=100, blank=True, null=True)
    related_object_type = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
    
    def mark_as_unread(self):
        self.is_read = False
        self.save()


# ---- Locations ----

# class Building(models.Model):
#     name = models.CharField(max_length=120, unique=True)

#     def __str__(self):
#         return str(self.name)


# class Floor(models.Model):
#     building = models.ForeignKey(Building, on_delete=models.CASCADE)
#     floor_number = models.IntegerField()

#     class Meta:
#         unique_together = ("building", "floor_number")

#     def __str__(self):
#         return f'{self.building.name} - Floor {self.floor_number}'


# class LocationFamily(models.Model):
#     name = models.CharField(max_length=120, unique=True)

#     def __str__(self):
#         return str(self.name)


# class LocationType(models.Model):
#     name = models.CharField(max_length=120, unique=True)

#     def __str__(self):
#         return str(self.name)


# class Location(models.Model):
#     family = models.ForeignKey(LocationFamily, on_delete=models.SET_NULL, null=True, blank=True)
#     type = models.ForeignKey(LocationType, on_delete=models.SET_NULL, null=True, blank=True)
#     building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)
#     floor = models.ForeignKey(Floor, on_delete=models.SET_NULL, null=True, blank=True)
#     name = models.CharField(max_length=160)
#     description = models.TextField(blank=True, null=True)
#     room_no = models.CharField(max_length=40, blank=True, null=True)
#     capacity = models.PositiveIntegerField(blank=True, null=True)

#     class Meta:
#         unique_together = ("building", "room_no")

#     def __str__(self):
#         return str(self.name)

class Building(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
    ]
    building_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False,unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='building_images/', null=True, blank=True)  # NEW
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active') 

    class Meta:
        db_table = 'building'
    
    @property
    def floors_count(self):
        return self.floors.count()   # thanks to related_name='floors'

    @property
    def rooms_count(self):
        return self.locations.count()  

    


class Floor(models.Model):
    floor_name=models.CharField(max_length=50,blank=False,null=False)
    floor_id = models.BigAutoField(primary_key=True)
    building = models.ForeignKey('Building', models.CASCADE,blank=False,null=False,related_name='floors')
    floor_number = models.IntegerField(blank=False, null=False)
    description = models.CharField(max_length=255, blank=True)  # e.g. “Lobby & Reception”
    rooms = models.PositiveIntegerField(default=0)
    occupancy = models.PositiveIntegerField(default=0)     # percent (0-100)
    is_active = models.BooleanField(default=True)
    
    @property
    def total_rooms(self):
        return self.locations.count()

    @property
    def occupied_rooms_count(self):
        return self.locations.filter(is_occupied=True).count()

    @property
    def occupancy_percent(self):
        total = self.total_rooms
        if total == 0:
            return 0
        return round((self.occupied_rooms_count / total) * 100, 2)

    class Meta:
        db_table = 'floor'
        constraints = [
            models.UniqueConstraint(
                fields=['building', 'floor_name'],
                name='unique_floor_per_building'
            )
        ]


class LocationFamily(models.Model):
    family_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)
    image = models.ImageField(upload_to="location_family/", blank=True, null=True) 
    
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'location_family'
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_location_family_name'
            )
        ]


class LocationType(models.Model):
    type_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120,blank=False, null=False)
    family = models.ForeignKey(LocationFamily, on_delete=models.CASCADE, related_name='types',null=False)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="location_types/", blank=True, null=True) 
    
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'location_type'
        constraints = [
            models.UniqueConstraint(
                fields=['family', 'name'],
                name='unique_type_per_building'
            )
        ]


class Location(models.Model):
    STATUS_CHOICES = [
    ('active', 'Active'),
    ('maintenance', 'Maintenance'),
    ('Inactive', 'Inactive'),
]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.CharField(max_length=255, blank=True, null=True)
    location_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50,blank=False, null=False)       # updated (was 160)
    family = models.ForeignKey(LocationFamily, on_delete=models.PROTECT,blank=True, null=True)
    # updated (was FK)
    type = models.ForeignKey(LocationType, on_delete=models.PROTECT, null=True, blank=True)
      # updated (was FK)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, blank=True, null=True,related_name='locations')
            # updated (was FK)
    pavilion = models.CharField(max_length=120, null=True, blank=True)   # added
    room_no = models.CharField(max_length=40,blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    building = models.ForeignKey('Building', models.CASCADE,blank=True, null=True,related_name='locations')  # kept for compatibility
    is_occupied = models.BooleanField(default=False)
    class Meta:
        db_table = 'location'
        constraints = [
            models.UniqueConstraint(
                fields=['building', 'name'],
                name='unique_location_name_per_building'
            )
        ]
        



# ---- Workflow ----

class RequestFamily(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return str(self.name)


class WorkFamily(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return str(self.name)


class Workflow(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return str(self.name)


class WorkflowStep(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    step_order = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    role_hint = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        ordering = ['workflow', 'step_order']
        unique_together = ("workflow", "step_order")

    def __str__(self):
        return f'{self.workflow.name} - {self.step_order}: {self.name}'


class WorkflowTransition(models.Model):
    from_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, related_name='transitions_from')
    to_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, related_name='transitions_to')
    condition_expr = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f'{self.from_step} -> {self.to_step}'


# ---- Checklist ----

# class Checklist(models.Model):
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return str(self.name)


# class ChecklistItem(models.Model):
#     checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
#     label = models.CharField(max_length=240, blank=True, null=True)
#     required = models.BooleanField(default=False)

#     def __str__(self):
#         return self.label or f'Item {self.pk}'


# ---- Requests ----

class RequestType(models.Model):
    request_type_id = models.BigAutoField(primary_key=True) 
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    workflow = models.ForeignKey(Workflow, on_delete=models.SET_NULL, null=True, blank=True)
    work_family = models.ForeignKey(WorkFamily, on_delete=models.SET_NULL, null=True, blank=True)
    request_family = models.ForeignKey(RequestFamily, on_delete=models.SET_NULL, null=True, blank=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.SET_NULL, null=True, blank=True)
    default_department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_request_types',
        help_text='Department that typically handles this request type.'
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.name)
    class Meta:
        db_table='request_type'

# class ReviewQueue(models.Model):
#     """
#     📩 Temporary holding area for incoming WhatsApp messages.
#     Admin reviews → moves to ServiceRequest.
#     """
#     guest_name = models.CharField(max_length=100, blank=True, null=True)
#     phone_number = models.CharField(max_length=50)
#     room_no = models.CharField(max_length=10, blank=True, null=True)
#     message_text = models.TextField()
#     matched_request_type = models.ForeignKey(RequestType, on_delete=models.SET_NULL, null=True, blank=True)
#     guest_info = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"Review #{self.id} - {self.phone_number}"
#     class Meta:
#         db_table='review_queue'
# class IncomingMessage(models.Model):
#     """Stores all WhatsApp messages (matched/unmatched) before classification"""
#     guest_name = models.CharField(max_length=100, blank=True)
#     phone_number = models.CharField(max_length=50)
#     room_no = models.CharField(max_length=50, blank=True)
#     body = models.TextField()
#     received_at = models.DateTimeField(default=timezone.now)
#     reviewed = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.guest_name or 'Guest'} ({self.phone_number})"
#     class Meta:
#         db_table="income"
from django.utils import timezone
from django.conf import settings

class TicketReview(models.Model):
    """Temporary holding model for requests before creating final ServiceRequest"""
    
    voucher = models.ForeignKey('Voucher', on_delete=models.SET_NULL, null=True, blank=True)
    guest_name = models.CharField(max_length=120, blank=True, null=True)
    room_no = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=False, null=False, db_index=True)
    request_text = models.TextField(blank=True, null=True)

    matched_request_type = models.ForeignKey('RequestType', on_delete=models.SET_NULL, null=True, blank=True)
    matched_department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=20, default='normal')

    # AI / rule confidence score
    match_confidence = models.FloatField(default=0.0)
    is_matched = models.BooleanField(default=False)

    review_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    moved_to_ticket = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TicketReview #{self.pk} - {self.guest_name or self.phone_number}"

    class Meta:
        db_table = "ticket_review"
        ordering = ['-created_at']

# from django.db import models
# from django.utils import timezone

# # Existing models: Voucher, RequestType, Department, DepartmentRequestSLA, ServiceRequest

# class UnclassifiedTicket(models.Model):
#     """
#     All incoming WhatsApp requests (matched or unmatched)
#     go here first for review.
#     """
#     voucher = models.ForeignKey("Voucher", on_delete=models.SET_NULL, null=True, blank=True)
#     guest_name = models.CharField(max_length=255, blank=True, null=True)
#     room_no = models.CharField(max_length=50, blank=True, null=True)
#     phone_number = models.CharField(max_length=50, blank=True, null=True)
#     body = models.TextField()
#     created_at = models.DateTimeField(default=timezone.now)
#     reviewed = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Ticket #{self.pk} - {self.guest_name or 'Unknown'}"
#     class Meta:
#         db_table="unclassified"
class RequestKeyword(models.Model):
    """Keyword mapping for automatic request type detection."""
    keyword = models.CharField(max_length=100, unique=True)
    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.CASCADE,
        related_name='keywords'
    )
    weight = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['keyword']
        db_table = 'request_keyword'

    def __str__(self):
        return f"{self.keyword} → {self.request_type.name}"


class ServiceRequest(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical'),  # Added critical priority
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
        ('escalated', 'Escalated'),
        ('rejected', 'Rejected'),
    ]
    # NOTE: guest_name field is removed to avoid duplication - use guest.full_name to access guest name via FK
    guest_name = models.CharField(max_length=100, null=True, blank=True)
    room_no = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    body = models.TextField(blank=True, null=True) 
    SOURCE_CHOICES = [
        ('web', 'Web'),
        ('dashboard', 'Dashboard'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('other', 'Other'),
    ]
    
    request_type = models.ForeignKey(RequestType, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    requester_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests_made')
    guest = models.ForeignKey('Guest', on_delete=models.SET_NULL, null=True, blank=True, related_name='service_requests')
    assignee_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests_assigned')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=20, blank=True, null=True, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=50, blank=True, null=True, choices=STATUS_CHOICES, default='pending')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='web')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    due_at = models.DateTimeField(blank=True, null=True)
    sla_hours = models.FloatField(default=24, help_text='SLA time in hours to resolve')
    sla_breached = models.BooleanField(default=False)
    response_sla_hours = models.FloatField(default=1, help_text='SLA time in hours to respond')
    response_sla_breached = models.BooleanField(default=False)
    resolution_sla_breached = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Request #{self.pk}'
    class Meta:
        db_table='service_request'
    

    def compute_due_at(self):
        """Compute due_at from created_at and sla_hours."""
        if self.created_at and self.sla_hours:
            return self.created_at + timezone.timedelta(hours=self.sla_hours)
        return None

    def save(self, *args, **kwargs):
        # Set SLA times based on priority and configuration if this is a new ticket
        if not self.pk:  # Only for new tickets
            self.set_sla_times()
            
        # Ensure due_at is set when creating or when sla_hours changes
        if not self.due_at:
            self.due_at = self.compute_due_at()

        # Update sla_breached flag if completed_at exists
        if self.completed_at and self.due_at:
            self.sla_breached = self.completed_at > self.due_at

        super().save(*args, **kwargs)

    def set_sla_times(self):
        """Set SLA times based on priority and configuration."""
        try:
            # First, try to get department/request-specific SLA configuration
            if self.department and self.request_type:
                from .models import DepartmentRequestSLA
                config = DepartmentRequestSLA.objects.get(
                    department=self.department,
                    request_type=self.request_type,
                    priority=self.priority
                )
                # Convert minutes to hours for the existing fields
                self.response_sla_hours = config.response_time_minutes / 60.0
                self.sla_hours = config.resolution_time_minutes / 60.0
                return
        except DepartmentRequestSLA.DoesNotExist:
            # If no department/request-specific config, continue to general config
            pass
        
        try:
            from .models import SLAConfiguration
            config = SLAConfiguration.objects.get(priority=self.priority)
            
            # Convert minutes to hours for the existing fields
            self.response_sla_hours = config.response_time_minutes / 60.0
            self.sla_hours = config.resolution_time_minutes / 60.0
        except SLAConfiguration.DoesNotExist:
            # Use default values if no configuration found
            if self.priority == 'critical':
                self.response_sla_hours = 5 / 60.0  # 5 minutes
                self.sla_hours = 5 / 60.0  # 5 minutes
            elif self.priority == 'high':
                self.response_sla_hours = 10 / 60.0  # 10 minutes
                self.sla_hours = 10 / 60.0  # 10 minutes
            elif self.priority == 'normal':
                self.response_sla_hours = 15 / 60.0  # 15 minutes
                self.sla_hours = 15 / 60.0  # 15 minutes
            elif self.priority == 'low':
                self.response_sla_hours = 20 / 60.0  # 20 minutes
                self.sla_hours = 20 / 60.0  # 20 minutes
            else:
                # Default values
                self.response_sla_hours = 1  # 1 hour
                self.sla_hours = 24  # 24 hours

    def assign_to_user(self, user):
        """Assign the ticket to a user and automatically accept it."""
        self.assignee_user = user
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        # Notify the assigned user
        self.notify_assigned_user()

    def assign_to_department(self, department):
        """Assign the ticket to a department and notify all staff."""
        self.department = department
        self.status = 'pending'  # Reset status to pending for department routing
        self.save()
        # Notify all staff in the department
        self.notify_department_staff()

    def accept_task(self):
        """Accept the assigned task."""
        # Since we're removing the 'assigned' state, we can accept directly from 'pending'
        if self.status == 'pending':
            self.status = 'accepted'
            self.accepted_at = timezone.now()
            # Save the changes
            self.save()

    def start_work(self):
        """Start working on the task."""
        if self.status == 'accepted':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()

    def complete_task(self, resolution_notes=None):
        """Mark the task as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if resolution_notes:
            self.resolution_notes = resolution_notes
        self.save()

    def close_task(self):
        """Close the task."""
        self.status = 'closed'
        self.closed_at = timezone.now()
        self.save()
        # Notify requester on closure
        self.notify_requester_on_closure()

    def escalate_task(self):
        """Escalate the task."""
        self.status = 'escalated'
        self.save()
        # Notify department leader on escalation
        self.notify_department_leader_on_escalation()

    def reject_task(self):
        """Reject the task."""
        self.status = 'rejected'
        self.save()

    def can_transition_to(self, new_status):
        """Check if the ticket can transition to the new status."""
        valid_transitions = {
            'pending': ['accepted'],
            'accepted': ['in_progress'],
            'in_progress': ['completed'],
            'completed': ['closed'],
            'closed': [],
            'escalated': ['accepted'],
            'rejected': ['accepted'],
        }
        return new_status in valid_transitions.get(self.status, [])

    def notify_department_staff(self):
        """Notify all staff members in the assigned department."""
        from .utils import create_bulk_notifications
        
        if not self.department:
            return
            
        # Get all users in the department
        department_users = User.objects.filter(userprofile__department=self.department)
        
        if department_users.exists():
            # Create notifications for all department staff
            create_bulk_notifications(
                recipients=department_users,
                title=f"New Ticket #{self.pk} Assigned: {self.request_type.name}",
                message=f"A new ticket #{self.pk} has been assigned to your department: {self.notes[:100]}...",
                notification_type='request',
                related_object=self
            )

    def notify_assigned_user(self):
        """Notify the user assigned to the ticket."""
        from .utils import create_notification
        
        if self.assignee_user:
            create_notification(
                recipient=self.assignee_user,
                title=f"Ticket #{self.pk} Assigned: {self.request_type.name}",
                message=f"You have been assigned ticket #{self.pk}: {self.notes[:100]}...",
                notification_type='request',
                related_object=self
            )

    def notify_requester_on_closure(self):
        """Notify the requester when ticket is closed."""
        from .utils import create_notification
        
        if self.requester_user:
            create_notification(
                recipient=self.requester_user,
                title=f"Ticket #{self.pk} Resolved: {self.request_type.name}",
                message=f"Your ticket #{self.pk} has been resolved: {self.resolution_notes or 'No resolution notes provided.'}",
                notification_type='success',
                related_object=self
            )

    def notify_department_leader_on_escalation(self):
        """Notify department leader when ticket is escalated."""
        from .utils import create_notification
        
        if self.department:
            # In a real implementation, you would identify the department leader
            # For now, we'll notify all department staff about the escalation
            department_users = User.objects.filter(userprofile__department=self.department)
            for user in department_users:
                create_notification(
                    recipient=user,
                    title=f"Ticket #{self.pk} Escalated: {self.request_type.name}",
                    message=f"Ticket #{self.pk} has been escalated. Please take immediate action.",
                    notification_type='warning',
                    related_object=self
                )

    def check_sla_breaches(self):
        """Check if SLA has been breached and update flags accordingly."""
        if not self.created_at:
            return
            
        now = timezone.now()
        
        # Check response SLA (time to acknowledge)
        if self.accepted_at:
            response_time = self.accepted_at - self.created_at
            response_sla_seconds = self.response_sla_hours * 3600  # Convert hours to seconds
            self.response_sla_breached = response_time.total_seconds() > response_sla_seconds
        elif self.status in ['accepted', 'in_progress', 'completed', 'closed']:
            # If in progress but not yet accepted, check response SLA from creation time
            response_time = now - self.created_at
            response_sla_seconds = self.response_sla_hours * 3600
            self.response_sla_breached = response_time.total_seconds() > response_sla_seconds
            
        # Check resolution SLA (time to resolve)
        if self.completed_at:
            resolution_time = self.completed_at - self.created_at
            resolution_sla_seconds = self.sla_hours * 3600
            self.resolution_sla_breached = resolution_time.total_seconds() > resolution_sla_seconds
        elif self.status in ['completed', 'closed']:
            # If marked as completed but completed_at not set, check against now
            resolution_time = now - self.created_at
            resolution_sla_seconds = self.sla_hours * 3600
            self.resolution_sla_breached = resolution_time.total_seconds() > resolution_sla_seconds
        elif self.status in ['in_progress', 'accepted', 'assigned']:
            # For open tickets, check if they're approaching or breaching SLA
            resolution_time = now - self.created_at
            resolution_sla_seconds = self.sla_hours * 3600
            self.resolution_sla_breached = resolution_time.total_seconds() > resolution_sla_seconds
            
        # Overall SLA breach is true if either response or resolution SLA is breached
        self.sla_breached = self.response_sla_breached or self.resolution_sla_breached

    def get_sla_status(self):
        """Get the current SLA status for display."""
        if self.status == 'closed':
            if self.sla_breached:
                return "Breached"
            else:
                return "Met"
        elif self.status in ['completed', 'in_progress', 'accepted', 'assigned']:
            if self.sla_breached:
                return "Breaching"
            else:
                return "On Track"
        else:
            return "Not Started"

    def get_time_left(self):
        """Get the time left before SLA breach."""
        if not self.created_at:
            return None
            
        now = timezone.now()
        
        # If already completed or closed, show time taken
        if self.completed_at or self.status == 'completed' or self.status == 'closed':
            completion_time = self.completed_at or self.closed_at or now
            time_taken = completion_time - self.created_at
            hours = int(time_taken.total_seconds() // 3600)
            minutes = int((time_taken.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m"
        
        # For open tickets, show time left until resolution SLA breach
        elapsed_time = now - self.created_at
        sla_seconds = self.sla_hours * 3600
        time_left_seconds = sla_seconds - elapsed_time.total_seconds()
        
        if time_left_seconds <= 0:
            return "Breached"
            
        # Convert to hours and minutes
        hours = int(time_left_seconds // 3600)
        minutes = int((time_left_seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"


class ServiceRequestStep(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('request', 'step')

    def __str__(self):
        return f'{self.request} - {self.step}'
    class Meta:
        db_table='service_request_step'


class ServiceRequestChecklist(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('request', 'item')

    def __str__(self):
        return f'{self.request} - {self.item}'
    class Meta:
        db_table='service_request_checklist'


class TicketComment(models.Model):
    """Internal comments on tickets that staff can add and view."""
    ticket = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='internal_comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket_comments'
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket_comment'
        ordering = ['-created_at']

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'Unknown'
        return f'Comment by {user_name} on Ticket #{self.ticket.pk}'


class WhatsAppConversation(models.Model):
    """Track per-phone WhatsApp conversation state for workflow handling."""
    STATE_IDLE = 'idle'
    STATE_AWAITING_MENU = 'awaiting_menu_selection'
    STATE_AWAITING_DESCRIPTION = 'awaiting_request_description'
    STATE_FEEDBACK_INVITED = 'feedback_invited'
    STATE_COLLECTING_FEEDBACK = 'collecting_feedback'

    STATE_CHOICES = [
        (STATE_IDLE, 'Idle'),
        (STATE_AWAITING_MENU, 'Awaiting Menu Selection'),
        (STATE_AWAITING_DESCRIPTION, 'Awaiting Request Description'),
        (STATE_FEEDBACK_INVITED, 'Feedback Invited'),
        (STATE_COLLECTING_FEEDBACK, 'Collecting Feedback'),
    ]

    GUEST_STATUS_UNKNOWN = 'unknown'
    GUEST_STATUS_PRE_CHECKIN = 'pre_checkin'
    GUEST_STATUS_CHECKED_IN = 'checked_in'
    GUEST_STATUS_CHECKED_OUT = 'checked_out'

    GUEST_STATUS_CHOICES = [
        (GUEST_STATUS_UNKNOWN, 'Unknown'),
        (GUEST_STATUS_PRE_CHECKIN, 'Pre Check-in'),
        (GUEST_STATUS_CHECKED_IN, 'Checked In'),
        (GUEST_STATUS_CHECKED_OUT, 'Checked Out'),
    ]

    phone_number = models.CharField(max_length=32, unique=True)
    guest = models.ForeignKey(
        'Guest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_conversations'
    )
    voucher = models.ForeignKey(
        'Voucher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_conversations'
    )
    current_state = models.CharField(
        max_length=48,
        choices=STATE_CHOICES,
        default=STATE_IDLE
    )
    last_known_guest_status = models.CharField(
        max_length=32,
        choices=GUEST_STATUS_CHOICES,
        default=GUEST_STATUS_UNKNOWN
    )
    context = models.JSONField(default=dict, blank=True)
    last_guest_message_at = models.DateTimeField(null=True, blank=True)
    last_system_message_at = models.DateTimeField(null=True, blank=True)
    menu_presented_at = models.DateTimeField(null=True, blank=True)
    welcome_sent_at = models.DateTimeField(null=True, blank=True)
    feedback_prompt_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        db_table = 'whatsapp_conversation'

    def __str__(self):
        return f'WhatsApp conversation {self.phone_number}'


class WhatsAppMessage(models.Model):
    """Audit log for inbound and outbound WhatsApp messages."""
    DIRECTION_INBOUND = 'inbound'
    DIRECTION_OUTBOUND = 'outbound'
    DIRECTION_CHOICES = [
        (DIRECTION_INBOUND, 'Inbound'),
        (DIRECTION_OUTBOUND, 'Outbound'),
    ]

    conversation = models.ForeignKey(
        WhatsAppConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    guest = models.ForeignKey(
        'Guest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_messages'
    )
    message_sid = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    direction = models.CharField(max_length=16, choices=DIRECTION_CHOICES)
    body = models.TextField(blank=True, null=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=32, blank=True, null=True)
    sent_at = models.DateTimeField(default=timezone.now)
    error = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-sent_at']
        db_table = 'whatsapp_message'

    def __str__(self):
        return f'{self.direction} message {self.message_sid or self.pk}'


class UnmatchedRequest(models.Model):
    """Messages that could not be auto-classified into a service request."""
    STATUS_PENDING = 'pending'
    STATUS_RESOLVED = 'resolved'
    STATUS_IGNORED = 'ignored'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_IGNORED, 'Ignored'),
    ]

    conversation = models.ForeignKey(
        WhatsAppConversation,
        on_delete=models.CASCADE,
        related_name='unmatched_requests'
    )
    guest = models.ForeignKey(
        'Guest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unmatched_requests'
    )
    phone_number = models.CharField(max_length=32)
    message_body = models.TextField()
    received_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_unmatched_requests'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_ticket = models.ForeignKey(
        ServiceRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='from_unmatched_requests'
    )
    request_type = models.ForeignKey(
        RequestType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unmatched_requests'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unmatched_requests'
    )
    keywords = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=32, default='whatsapp')
    context = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-received_at']
        db_table = 'unmatched_request'

    def mark_resolved(self, user=None, ticket=None, save=True):
        """Helper to mark the unmatched request as resolved."""
        self.status = self.STATUS_RESOLVED
        self.resolved_by = user
        self.resolved_at = timezone.now()
        if ticket is not None:
            self.created_ticket = ticket
        if save:
            self.save(update_fields=['status', 'resolved_by', 'resolved_at', 'created_ticket'])


# ---- Guests ----

class Guest(models.Model):
    full_name = models.CharField(max_length=160, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Enhanced check-in/checkout with time support
    checkin_date = models.DateField(blank=True, null=True)  # Legacy date field
    checkout_date = models.DateField(blank=True, null=True)  # Legacy date field
    checkin_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Check-in Date & Time")
    checkout_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Check-out Date & Time")
    
    # Guest Details QR Code - stored as base64 in database
    details_qr_code = models.TextField(blank=True, null=True, verbose_name="Guest Details QR Code (Base64)")
    details_qr_data = models.TextField(blank=True, null=True, verbose_name="Guest Details QR Data")
    
    breakfast_included = models.BooleanField(default=False)
    guest_id = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True)  # Hotel guest ID
    package_type = models.CharField(max_length=50, blank=True, null=True)  # Package or room type
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['guest_id']),
            models.Index(fields=['room_number']),
            models.Index(fields=['checkin_date', 'checkout_date']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Check date fields (legacy)
        if self.checkin_date and self.checkout_date:
            if self.checkout_date <= self.checkin_date:
                raise ValidationError('Checkout date must be after check-in date.')
        
        # Check datetime fields (new)
        if self.checkin_datetime and self.checkout_datetime:
            if self.checkout_datetime <= self.checkin_datetime:
                raise ValidationError('Check-out datetime must be after check-in datetime.')
        
        # Sync date fields with datetime fields
        if self.checkin_datetime and not self.checkin_date:
            self.checkin_date = self.checkin_datetime.date() if hasattr(self.checkin_datetime, "date") else None
        if self.checkout_datetime and not self.checkout_date:
            self.checkout_date = self.checkout_datetime.date() if hasattr(self.checkout_datetime, "date") else None
        
        if self.phone and len(str(self.phone)) < 10:
            raise ValidationError('Phone number must be at least 10 digits.')

    def get_current_status(self, reference_time=None):
        """
        Determine the guest's stay status relative to the provided reference time.

        Returns one of: 'checked_in', 'checked_out', 'pre_checkin', 'unknown'.
        """
        from datetime import datetime, time as time_cls

        reference_time = reference_time or timezone.now()

        checkin_dt = self.checkin_datetime
        checkout_dt = self.checkout_datetime

        if not checkin_dt and self.checkin_date:
            aware_checkin = datetime.combine(self.checkin_date, time_cls(15, 0))
            if timezone.is_naive(aware_checkin):
                aware_checkin = timezone.make_aware(aware_checkin, timezone.get_current_timezone())
            checkin_dt = aware_checkin

        if not checkout_dt and self.checkout_date:
            aware_checkout = datetime.combine(self.checkout_date, time_cls(11, 0))
            if timezone.is_naive(aware_checkout):
                aware_checkout = timezone.make_aware(aware_checkout, timezone.get_current_timezone())
            checkout_dt = aware_checkout

        if checkin_dt and checkout_dt:
            if checkin_dt <= reference_time <= checkout_dt:
                return 'checked_in'
            if reference_time < checkin_dt:
                return 'pre_checkin'
            if reference_time > checkout_dt:
                return 'checked_out'

        if checkin_dt and reference_time < checkin_dt:
            return 'pre_checkin'
        if checkout_dt and reference_time > checkout_dt:
            return 'checked_out'
        return 'unknown'

    def is_checked_in(self):
        return self.get_current_status() == 'checked_in'

    def has_checked_out(self):
        return self.get_current_status() == 'checked_out'

    def __str__(self):
        return str(self.full_name or f'Guest {self.pk}')
    
    def save(self, *args, **kwargs):
        # Generate unique guest ID if not provided
        if not self.guest_id:
            import random
            import string
            while True:
                guest_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Guest.objects.filter(guest_id=guest_id).exists():
                    self.guest_id = guest_id
                    break
        
        # Call clean method for validation
        self.full_clean()
        super().save(*args, **kwargs)
    
    def generate_details_qr_code(self, size='xxlarge'):
        """Generate QR code with all guest details and store as base64"""
        from .utils import generate_guest_details_qr_base64, generate_guest_details_qr_data
        
        try:
            # Generate QR data and base64 image
            self.details_qr_data = generate_guest_details_qr_data(self)
            self.details_qr_code = generate_guest_details_qr_base64(self, size=size)
            self.save(update_fields=['details_qr_data', 'details_qr_code'])
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to generate guest details QR code for {self.guest_id}: {str(e)}')
            return False
    
    def get_details_qr_data_url(self):
        """Get data URL for guest details QR code"""
        if self.details_qr_code:
            return f"data:image/png;base64,{self.details_qr_code}"
        return None
    
    def has_qr_code(self):
        """Check if guest has a QR code"""
        return bool(self.details_qr_code)


class GuestComment(models.Model):
    guest = models.ForeignKey("Guest", on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.CharField(max_length=20)
    source = models.CharField(max_length=20)
    rating = models.PositiveIntegerField(blank=True, null=True)
    comment_text = models.TextField()
    linked_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment {self.pk}'


class FeedbackQuestion(models.Model):
    """Questions presented to guests during feedback collection."""
    QUESTION_TYPE_RATING = 'rating'
    QUESTION_TYPE_TEXT = 'text'
    QUESTION_TYPE_BOOLEAN = 'boolean'
    QUESTION_TYPE_CHOICES = [
        (QUESTION_TYPE_RATING, 'Rating (1-5)'),
        (QUESTION_TYPE_TEXT, 'Free Text'),
        (QUESTION_TYPE_BOOLEAN, 'Yes / No'),
    ]

    prompt = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default=QUESTION_TYPE_TEXT
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        db_table = 'feedback_question'

    def __str__(self):
        return f'Question #{self.pk}: {self.prompt[:40]}'


class FeedbackSession(models.Model):
    """Session tracking guest feedback via WhatsApp."""
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    conversation = models.ForeignKey(
        WhatsAppConversation,
        on_delete=models.CASCADE,
        related_name='feedback_sessions'
    )
    guest = models.ForeignKey(
        'Guest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_sessions'
    )
    booking = models.ForeignKey(
        'Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_sessions'
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    current_question_index = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'feedback_session'

    def __str__(self):
        return f'Feedback session {self.pk} ({self.get_status_display()})'

    @property
    def is_active(self):
        return self.status in {self.STATUS_PENDING, self.STATUS_ACTIVE}


class FeedbackResponse(models.Model):
    """Stores responses captured during feedback sessions."""
    session = models.ForeignKey(
        FeedbackSession,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    question = models.ForeignKey(
        FeedbackQuestion,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    answer = models.TextField()
    received_at = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('session', 'question')
        ordering = ['received_at']
        db_table = 'feedback_response'

    def __str__(self):
        return f'Response #{self.pk} for session {self.session_id}'


# ---- Vouchers ----

# class Voucher(models.Model):
#     voucher_code = models.CharField(max_length=50, unique=True, blank=True)
#     guest_name = models.CharField(max_length=100)
#     room_number = models.CharField(max_length=10, blank=True, null=True)
#     issue_date = models.DateTimeField(default=timezone.now)
#     expiry_date = models.DateField()
#     redeemed = models.BooleanField(default=False)
#     redeemed_at = models.DateTimeField(blank=True, null=True)
#     qr_image = models.TextField(blank=True, null=True)  # Base64 encoded QR image
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_vouchers')  # Add this field
# class Voucher(models.Model):
#     voucher_code = models.CharField(max_length=50, unique=True, blank=True)
#     guest_name = models.CharField(max_length=100, blank=True, null=True)
#     room_number = models.CharField(max_length=10, blank=True, null=True)
#     issue_date = models.DateTimeField(default=timezone.now)
#     expiry_date = models.DateField(default=timezone.now)
#     redeemed = models.BooleanField(default=False)
#     redeemed_at = models.DateTimeField(blank=True, null=True)
#     qr_image = models.TextField(blank=True, null=True)  # Base64 encoded QR image
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_vouchers')  # Add this field

#     def __str__(self):
#         return f"{self.guest_name} - {self.voucher_code}"

#     def is_valid(self):
#         """Check if the voucher is still valid (not expired and not redeemed)"""
#         return not self.redeemed and self.expiry_date >= timezone.now().date()

#     def save(self, *args, **kwargs):
#         if not self.voucher_code:
#             self.voucher_code = self.generate_unique_code()
#         super().save(*args, **kwargs)

#     def generate_unique_code(self):
#         """Generate a unique voucher code"""
#         while True:
#             code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
#             if not Voucher.objects.filter(voucher_code=code).exists():
#                 return code


# class VoucherScan(models.Model):
#     voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='scans')
#     scanned_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
#     scanned_at = models.DateTimeField(auto_now_add=True)
#     notes = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return f"Scan of {self.voucher.voucher_code} at {self.scanned_at}"


# ---- Complaints & Reviews ----

class Complaint(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    due_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Complaint #{self.pk}: {self.subject}"


class Review(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Review #{self.pk}: {self.rating} stars"



# class GymMember(models.Model):
#     full_name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=15)
#     email = models.EmailField(max_length=100, blank=True, null=True)
#     start_date = models.DateField(blank=True, null=True)
#     end_date = models.DateField(blank=True, null=True)
#     status = models.CharField(max_length=50, blank=True, null=True)
#     plan_type = models.CharField(max_length=50, blank=True, null=True)

#     def __str__(self):  # pyright: ignore[reportIncompatibleMethodOverride]
#         return self.full_name


# class GymVisitor(models.Model):
#     full_name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=15, blank=True, null=True)
#     email = models.EmailField(max_length=100, blank=True, null=True)
#     registered_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):  # pyright: ignore[reportIncompatibleMethodOverride]
#         return self.full_name


# class GymVisit(models.Model):
#     member = models.ForeignKey(GymMember, on_delete=models.SET_NULL, null=True, blank=True)
#     visitor = models.ForeignKey(GymVisitor, on_delete=models.SET_NULL, null=True, blank=True)
#     visit_at = models.DateTimeField(blank=True, null=True)
#     checked_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
#     notes = models.CharField(max_length=240, blank=True, null=True)

#     def __str__(self):
#         return f'Visit {self.pk}'

from django.db import models
from django.contrib.auth.models import User
import io, base64, qrcode
# =========================
# GYM MEMBER
# =========================
class GymMember(models.Model):
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
    ]
    member_id = models.BigAutoField(primary_key=True)
    customer_code = models.CharField(max_length=50, unique=True, blank=False, null=False)  # like FGS0001
    full_name = models.CharField(max_length=100, blank=False, null=False)
    nik = models.CharField(max_length=20, blank=True, null=True)  # national ID
    address = models.CharField(max_length=255, blank=False, null=False)
    city = models.CharField(max_length=100, blank=True, null=True)
    place_of_birth = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)  # Male/Female
    occupation = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=False, null=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    pin = models.CharField(max_length=10, blank=True, null=True)
    password = models.CharField(max_length=128, blank=False, null=False)
    qr_code = models.TextField(blank=True, null=True)  # store QR data
    qr_code_image = models.ImageField(upload_to="qr_codes/", null=True, blank=True)  # base64 or image path
    confirm_password = models.CharField(max_length=128, blank=False, null=False)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")
    plan_type = models.CharField(max_length=50, blank=True, null=True)
    qr_expired = models.BooleanField(default=False) 

    created_at = models.DateTimeField(auto_now_add=True)
       # Manual entry if needed
    expiry_date = models.DateField(blank=True, null=True)  # Auto 3 months validity
    check_in_date = models.DateField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)
    unique_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True) 

    

    # Scan tracking
    scan_count = models.IntegerField(default=0)
    scan_history = models.JSONField(default=list, blank=True)
    country_code = models.CharField(max_length=5, default="91")
    

    class Meta:
        db_table = 'gym_member'

    def __str__(self):
        return f"{self.customer_code} - {self.full_name}"
    
    
    def is_expired(self):
        if not self.expiry_date:
            return False
        expiry_dt = datetime.combine(self.expiry_date, time(23, 59))
        if timezone.is_naive(expiry_dt):
            expiry_dt = timezone.make_aware(expiry_dt, timezone.get_current_timezone())
        return timezone.now() > expiry_dt

    from datetime import date, datetime

    def is_valid_today(self, max_scans_per_day=3):
        today = date.today().isoformat()
        if self.is_expired():
            return False
    
    # Count today's scans (assuming scan_history stores timestamps as ISO strings)
        today_scans = [scan for scan in (self.scan_history or []) if scan.startswith(today)]
        if len(today_scans) >= max_scans_per_day:
             return False
    
    # Must be between start_date and expiry_date
        if self.start_date and self.expiry_date:
            return self.start_date <= date.today() <= self.expiry_date
        return True


    from datetime import datetime, date

    def mark_scanned_today(self, max_scans_per_day=3):
        if not self.is_valid_today(max_scans_per_day=max_scans_per_day):
            return False
    
    # Ensure scan_history is a list
        self.scan_history = list(self.scan_history or [])
    
    # Store full timestamp instead of just date
        self.scan_history.append(datetime.now().isoformat())
        self.scan_count = (self.scan_count or 0) + 1
        self.save(update_fields=["scan_history", "scan_count"])
        return True


    def status_display(self):
        if self.is_expired():
            return format_html('<span style="color:red;font-weight:bold;">Expired</span>')
        return format_html('<span style="color:green;font-weight:bold;">Active</span>')


# =========================
# GYM VISITOR (non-member)
# =========================
class GymVisitor(models.Model):
    visitor_id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=100, blank=False, null=False)
    phone = models.CharField(max_length=20, blank=False, null=False)
    email = models.CharField(max_length=100, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gym_visitor'

    def __str__(self):
        return self.full_name


# =========================
# GYM VISIT (log entry)
# =========================
class GymVisit(models.Model):
    visit_id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey('GymMember', models.DO_NOTHING, blank=True, null=True)
    visitor = models.ForeignKey('GymVisitor', models.DO_NOTHING, blank=True, null=True)
    visit_at = models.DateTimeField(auto_now_add=True)
    checked_by_user = models.ForeignKey(User, models.DO_NOTHING, blank=False, null=False)
    notes = models.CharField(max_length=240, blank=True, null=True)

    class Meta:
        db_table = 'gym_visit'

    def __str__(self):
        return f"Visit {self.visit_id} - {self.visit_at}"


# ---- Booking System ----

class Booking(models.Model):
    """Guest booking/reservation model"""
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    room_number = models.CharField(max_length=20)
    booking_reference = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['check_in', 'check_out']),
            models.Index(fields=['room_number']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            import random
            import string
            while True:
                ref = 'BK' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Booking.objects.filter(booking_reference=ref).exists():
                    self.booking_reference = ref
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.guest.full_name}"


class SLAConfiguration(models.Model):
    """Model to store configurable SLA times for different priority levels"""
    priority = models.CharField(max_length=20, unique=True, choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ])
    response_time_minutes = models.PositiveIntegerField(
        help_text="Response time in minutes"
    )
    resolution_time_minutes = models.PositiveIntegerField(
        help_text="Resolution time in minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SLA Config - {self.get_priority_display()}"

    class Meta:
        verbose_name = "SLA Configuration"
        verbose_name_plural = "SLA Configurations"
    class Meta:
        db_table='slaconfiguration'


class DepartmentRequestSLA(models.Model):
    """Model to store configurable SLA times for specific department and request type combinations"""
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='sla_configurations')
    request_type = models.ForeignKey('RequestType', on_delete=models.CASCADE, related_name='sla_configurations')
    priority = models.CharField(max_length=20, choices=[
        ('critical', 'Critical'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ])
    response_time_minutes = models.PositiveIntegerField(
        help_text="Response time in minutes"
    )
    resolution_time_minutes = models.PositiveIntegerField(
        help_text="Resolution time in minutes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('department', 'request_type', 'priority')
        verbose_name = "Department Request SLA"
        verbose_name_plural = "Department Request SLAs"

    def __str__(self):
        return f"{self.department.name} - {self.request_type.name} ({self.get_priority_display()})"
    class Meta:
        db_table='department_request_sla'


class TwilioSettings(models.Model):
    """Store Twilio WhatsApp credentials configurable via the dashboard."""

    account_sid = models.CharField(max_length=64, blank=True, default='')
    auth_token = models.CharField(max_length=128, blank=True, default='')
    api_key_sid = models.CharField(max_length=64, blank=True, default='')
    api_key_secret = models.CharField(max_length=128, blank=True, default='')
    whatsapp_from = models.CharField(max_length=34, blank=True, default='')
    test_to_number = models.CharField(max_length=34, blank=True, default='')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='twilio_settings_updates'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Twilio Setting"
        verbose_name_plural = "Twilio Settings"
        db_table = 'twilio_settings'

    def __str__(self):
        return "Twilio Settings"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# # Legacy models for backward compatibility (will be deprecated)
# class BreakfastVoucher(models.Model):
#     """Legacy model - use Voucher instead"""
#     code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
#     guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True, blank=True)
#     room_no = models.CharField(max_length=20, blank=True, null=True)
#     location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
#     qr_image = models.ImageField(upload_to="vouchers/", blank=True, null=True)
#     qty = models.PositiveIntegerField(default=1)
#     valid_from = models.DateField(blank=True, null=True)
#     valid_to = models.DateField(blank=True, null=True)
#     redeemed_on = models.DateField(blank=True, null=True)
#     status = models.CharField(max_length=20, blank=True, null=True, choices=[
#         ("active", "Active"),
#         ("redeemed", "Redeemed"),
#         ("expired", "Expired"),
#     ], default="active")
#     sent_whatsapp = models.BooleanField(default=False)
#     sent_at = models.DateTimeField(blank=True, null=True)
#     created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)

#     class Meta:
#         verbose_name = 'Legacy Breakfast Voucher'
#         verbose_name_plural = 'Legacy Breakfast Vouchers'
#         ordering = ['-created_at']

#     def is_valid(self):
#         today = timezone.now().date()
#         return (self.valid_from and self.valid_to and 
#                 self.valid_from <= today <= self.valid_to and 
#                 self.status == 'active' and
#                 (self.redeemed_on != today))
    
#     def __str__(self):
#         return f'Legacy Voucher {self.code}'

# class BreakfastVoucherScan(models.Model):
#     """Legacy scan model - use VoucherScan instead"""
#     voucher = models.ForeignKey(BreakfastVoucher, on_delete=models.CASCADE, related_name="legacy_scans")
#     scanned_at = models.DateTimeField(auto_now_add=True)
#     scanned_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="legacy_voucher_scans"
#     )
#     source = models.CharField(max_length=50, default="web")

#     class Meta:
#         verbose_name = 'Legacy Breakfast Voucher Scan'
#         verbose_name_plural = 'Legacy Breakfast Voucher Scans'
#         ordering = ['-scanned_at']

#     def __str__(self):
#         return f"Legacy Scan {self.id} for {self.voucher.code}"

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import os
from django.utils.html import format_html
import string
import random
from datetime import time, timedelta, date, datetime
from django.db import models, IntegrityError, transaction
from django.utils import timezone
import uuid
import os
from django.utils.html import format_html

def random_code(prefix="BKT", length=6):
    chars = string.ascii_uppercase + string.digits
    return prefix + ''.join(random.choices(chars, k=length))
def qr_upload_path(instance, filename):
    return os.path.join("qrcodes", filename)

class Voucher(models.Model):
    # keep id as default 'id' (you previously had id)

    voucher_code = models.CharField(max_length=100, unique=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    guest_name = models.CharField(max_length=100,blank=False, null=False)
    country_code = models.CharField(max_length=5, default="91")  # Example: 91 for India

    phone_number = models.CharField(max_length=15,blank=False, null=False) 
    room_no = models.CharField(max_length=100,blank=False, null=False)   # added
    check_in_date = models.DateField(blank=True, null=True)            # added
    check_out_date = models.DateField(blank=True, null=True)           # added
    expiry_date = models.DateField(blank=True, null=True)              # existing-ish field (keep)
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(blank=True, null=True)
    qr_code = models.TextField(blank=True, null=True)  # url / content
    qr_code_image = models.ImageField(upload_to=qr_upload_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    adults = models.IntegerField(default=1,blank=False, null=False)   
    kids = models.IntegerField(default=0,blank=False, null=False) 
    is_used = models.BooleanField(default=False)
    email = models.EmailField(null=True, blank=True)
    qr_sent_whatsapp = models.BooleanField(default=False)
    scan_count = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0) 
    valid_dates = models.JSONField(default=list)       # e.g. ["2025-09-07", "2025-09-08"]
    scan_history = models.JSONField(default=list,blank=True)      
    include_breakfast = models.BooleanField(default=False)
    class Meta:
        db_table = "voucher"
    
    # def save(self, *args, **kwargs):
       
    #     # ✅ Always update quantity before saving
    #     self.quantity = (self.adults or 0) + (self.kids or 0)
        
        
    #     super().save(*args, **kwargs)

    # def is_valid_now(self):
    #     today = timezone.localdate()
    #     # valid if within stay dates or expiry_date
    #     if self.check_in_date and self.check_out_date:
    #         return self.check_in_date <= today <= self.check_out_date
    #     if self.expiry_date:
    #         return today <= self.expiry_date
    #     return True

    # def mark_redeemed(self, user=None):
    #     self.redeemed = True
    #     self.redeemed_at = timezone.now()
    #     self.save(update_fields=["redeemed", "redeemed_at"])
    # def __str__(self):
    #     return f"{self.voucher_code} - {self.guest_name}"

    # def is_used_display(self):
    #     if self.is_used:
    #         return format_html('<span style="color:red; font-weight:bold;">Expired</span>')
    #     return format_html('<span style="color:green; font-weight:bold;">Active</span>')
    # is_used_display.short_description = "Voucher Status"
    
     

    def _generate_unique_code(self, prefix="BF"):
        # tries a few times and returns a code
        for _ in range(10):
            code = random_code(prefix=prefix, length=6)
            # quick existence check to avoid a save attempt when already used
            if not Voucher.objects.filter(voucher_code=code).exists():
                return code
        # fallback to UUID if unlucky
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    def save(self, *args, **kwargs):
        self.quantity = (self.adults or 0) + (self.kids or 0)
        if self.valid_dates is None:
            self.valid_dates = []
        if self.scan_history is None:
            self.scan_history = []

        # Auto-generate valid_dates (check-in → check-out inclusive)
        if self.check_in_date and self.check_out_date and not self.valid_dates:
            dates = []
            current = self.check_in_date
            while current <= self.check_out_date:
                dates.append(current.isoformat())
                current += timedelta(days=1)
            self.valid_dates = dates

        if not self.voucher_code:
            self.voucher_code = self._generate_unique_code()

        super().save(*args, **kwargs)

    # -------------------------------
    # VALIDATION RULES
    # -------------------------------
    def is_expired(self):
    
     if not self.check_out_date:
        return False

     expiry_dt = datetime.combine(self.check_out_date, time(23, 59))

    # Make sure expiry_dt is timezone-aware
     if timezone.is_naive(expiry_dt):
        expiry_dt = timezone.make_aware(expiry_dt, timezone.get_current_timezone())

     return timezone.now() > expiry_dt


    def is_valid_today(self):
        today = timezone.localdate().isoformat()

    # 1️⃣ Expired
        if self.is_expired():
            return False

    # 2️⃣ Quantity exhausted
        scans_today = len([
        s for s in (self.scan_history or [])
        if s.get("date") == today
    ])

        if scans_today >= self.quantity:
            return False

    # 3️⃣ Date must be valid
        if today not in (self.valid_dates or []):
            return False

    # 4️⃣ Breakfast timing rule (check-in day only)
        if self.include_breakfast:
            now = timezone.localtime().time()
            if self.check_in_date and date.today() == self.check_in_date:
                if now > time(11, 00):
                    return False

        return True

    # def is_valid_today(self):
    
    #  today = timezone.localdate().isoformat()

    # # 1. Not valid if expired
    #  if self.is_expired():
    #     return False

    # # 2. Only one scan per day
    #  if today in (self.scan_history or []):
    #     return False

    # # 3. Date must be in valid_dates
    #  if today not in (self.valid_dates or []):
    #     return False

    # # 4. Special rule for breakfast
    #  if self.include_breakfast:
    #     now = timezone.localtime().time()
    #     if self.check_in_date and date.today() == self.check_in_date:
    #         # Must check-in before 11:30 AM if breakfast included
    #         if now > time(11, 30):
    #             return False  # missed breakfast window

    # # ✅ Otherwise, valid
    #  return True


    def mark_scanned_today(self):
        """Mark today's scan if valid"""
        if self.is_valid_today():
            today = date.today().isoformat()
            if today not in (self.scan_history or []):
                self.scan_history = list(self.scan_history or [])
                self.scan_history.append(today)
                self.save(update_fields=["scan_history"])
                return True
        return False

    def is_used_display(self):
        if self.is_expired():
            return format_html('<span style="color:red;font-weight:bold;">Expired</span>')
        return format_html('<span style="color:green;font-weight:bold;">Active</span>')

    is_used_display.short_description = "Voucher Status"
    def used_scans(self):
    
        if not self.include_breakfast:
            return 0

        today = timezone.localdate().isoformat()

        return len([
            s for s in (self.scan_history or [])
            if s.get("date") == today
    ])
    def scans_on_date(self, target_date=None):
        target_date = target_date or timezone.localdate().isoformat()
        return [s for s in (self.scan_history or []) if s.get("date") == target_date]

    def scans_in_range(self, start_date, end_date):
        """Return scans between start_date and end_date inclusive"""
        scans = []
        for s in (self.scan_history or []):
            d = s.get("date")
            if d >= start_date.isoformat() and d <= end_date.isoformat():
                scans.append(s)
        return scans

    def total_scans_today(self):
        """Planned scans today (quantity for today if voucher valid)"""
        today = timezone.localdate().isoformat()
        if self.include_breakfast and today in (self.valid_dates or []):
            return self.quantity
        return 0

    def redeemed_today(self):
        """Actual scans done today"""
        return len(self.scans_on_date())

    def left_to_redeem_today(self):
        return max(0, self.total_scans_today() - self.redeemed_today())

    def total_scans_week(self, week_start, week_end):
        """Planned scans this week"""
        if not self.include_breakfast:
            return 0
        count = 0
        for d in (self.valid_dates or []):
            if week_start.isoformat() <= d <= week_end.isoformat():
                count += self.quantity
        return count

    def redeemed_week(self, week_start, week_end):
        return len(self.scans_in_range(week_start, week_end))


    def remaining_scans(self):
        if not self.include_breakfast:
            return 0

        today = timezone.localdate().isoformat()
        scans_today = len([
            s for s in (self.scan_history or [])
            if s.get("date") == today
        ])
        return max(0, self.quantity - scans_today)


    def scanned_users_display(self):
    
        users = []
        for s in self.scan_history or []:
            if "username" in s:
                users.append(s["username"])
        return ", ".join(sorted(set(users))) if users else "-"


    def generate_qr_code(self, size='xxlarge'):
        """Generate QR code image and save to file system"""
        from .utils import generate_qr_code
        import io
        from django.core.files.base import ContentFile
        
        try:
            # Generate QR data
            qr_data = f"Voucher: {self.voucher_code}\nGuest: {self.guest_name}\nRoom: {self.room_no}\nValid until: {self.check_out_date}"
            
            # Generate QR code as base64
            qr_base64 = generate_qr_code(qr_data, size=size)
            
            # Also save as image file
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Size mapping
            size_map = {
                'small': (100, 100),
                'medium': (200, 200),
                'large': (300, 300),
                'xlarge': (400, 400),
                'xxlarge': (500, 500)
            }
            size_px = size_map.get(size, size_map['medium'])
            
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize(size_px)
            
            # Save to ImageField
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            filename = f"voucher_{self.voucher_code}_{size}.png"
            self.qr_code_image.save(filename, ContentFile(buffer.getvalue()), save=True)
            
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to generate QR code for voucher {self.voucher_code}: {str(e)}')
            return False



# class MasterUser(User):
#     class Meta:
#         proxy = True
#         verbose_name = 'Master User'
#         verbose_name_plural = 'Master Users'


# class MasterLocation(Location):
#     class Meta:
#         proxy = True
#         verbose_name = 'Master Location'
#         verbose_name_plural = 'Master Locations'


# ---- Section Permissions ----

class Section(models.Model):
    """
    Model representing sidebar sections for permission management.
    Each section can have view, add, change, delete permissions.
    """
    name = models.CharField(max_length=50, unique=True, db_index=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'section'
        ordering = ['name']
        verbose_name = 'Section'
        verbose_name_plural = 'Sections'
    
    def __str__(self):
        return self.display_name
    
    def get_permission_codename(self, action):
        """Get permission codename for an action (view, add, change, delete)"""
        return f'{action}_{self.name}'
    
    @classmethod
    def get_or_create_sections(cls):
        """Get or create all standard sidebar sections"""
        sections = [
            ('users', 'Users', 'Manage Users section'),
            ('locations', 'Locations', 'Locations management section'),
            ('tickets', 'Tickets', 'Service Requests/Tickets section'),
            ('my_tickets', 'My Tickets', 'My Tickets section'),
            ('requests', 'Predefined Requests', 'Predefined Requests configuration section'),
            ('sla', 'SLA Configuration', 'SLA Configuration section'),
            ('messaging', 'Messaging Setup', 'Messaging Setup section'),
            ('gym', 'Gym Management', 'Gym Management section'),
            ('integrations', 'Integrations', 'Integrations section'),
            ('analytics', 'Analytics', 'Analytics section'),
            ('performance', 'Performance', 'Performance Dashboard section'),
            ('feedback', 'Feedback', 'Feedback/Reviews section'),
            ('breakfast_voucher', 'Breakfast Voucher', 'Breakfast Voucher section'),
            ('dashboard', 'Dashboard', 'Dashboard overview section'),
        ]
        
        created_sections = []
        for name, display_name, description in sections:
            section, created = cls.objects.get_or_create(
                name=name,
                defaults={
                    'display_name': display_name,
                    'description': description,
                    'is_active': True
                }
            )
            created_sections.append(section)
        return created_sections