import qrcode
import base64
from io import BytesIO
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from .models import Notification

def user_in_group(user, group_name):
    """Check if user is in a specific group"""
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists())

def group_required(group_names):
    """
    Decorator for views that checks whether a user belongs to any of the given groups.
    If not, raises PermissionDenied or redirects to login.
    """
    if not isinstance(group_names, (list, tuple)):
        group_names = [group_names]
    
    def check_group(user):
        if user.is_superuser:
            return True
        return any(user_in_group(user, group_name) for group_name in group_names)
    
    return user_passes_test(check_group)

def admin_required(view_func):
    """Decorator for admin-only views"""
    def wrapper(request, *args, **kwargs):
        if not user_in_group(request.user, getattr(settings, "ADMINS_GROUP", "Admins")):
            if not request.user.is_authenticated:
                return redirect('login')
            else:
                raise PermissionDenied("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper

def generate_qr_code(data, size='medium'):
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
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
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str

def generate_voucher_qr_data(voucher):
    """Generate QR data for voucher"""
    return f"Voucher: {voucher.voucher_code}\nGuest: {voucher.guest_name}\nRoom: {voucher.room_number}"

def generate_voucher_qr_base64(voucher, size='xxlarge'):
    """Generate QR code for voucher and return as base64 string"""
    data = generate_voucher_qr_data(voucher)
    return generate_qr_code(data, size)

def generate_guest_details_qr_data(guest):
    """Generate QR data for guest details"""
    return f"Guest ID: {guest.guest_id}\nName: {guest.full_name}\nRoom: {guest.room_number}\nCheck-in: {guest.checkin_date}\nCheck-out: {guest.checkout_date}"

def generate_guest_details_qr_base64(guest, size='xxlarge'):
    """Generate QR code for guest details and return as base64 string"""
    data = generate_guest_details_qr_data(guest)
    return generate_qr_code(data, size)

# Notification utility functions
def create_notification(recipient, title, message, notification_type='info', related_object=None):
    """
    Create a notification for a user AND send Firebase push notification
    
    Args:
        recipient: User object to receive the notification
        title: Title of the notification
        message: Message content of the notification
        notification_type: Type of notification (info, warning, error, success, request, voucher, system)
        related_object: Optional related object (e.g., ServiceRequest, Voucher)
    """
    notification_data = {
        'recipient': recipient,
        'title': title,
        'message': message,
        'notification_type': notification_type
    }
    
    if related_object:
        notification_data['related_object_id'] = related_object.id
        notification_data['related_object_type'] = related_object.__class__.__name__
    
    # Create in-app notification
    notification = Notification.objects.create(**notification_data)
    
    # Try to send Firebase push notification
    try:
        from .fcm_utils import send_push_notification_to_user
        
        # Prepare data for Firebase
        fcm_data = {
            'notification_id': str(notification.id),
            'type': notification_type,
        }
        
        if related_object:
            fcm_data['related_object_id'] = str(related_object.id)
            fcm_data['related_object_type'] = related_object.__class__.__name__
        
        # Send Firebase push notification
        send_push_notification_to_user(
            user=recipient,
            title=title,
            body=message,
            data=fcm_data
        )
    except Exception as e:
        # If Firebase fails, log it but don't fail the notification creation
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Could not send Firebase push notification: {e}")
    
    return notification

def create_bulk_notifications(recipients, title, message, notification_type='info', related_object=None):
    """
    Create notifications for multiple users AND send Firebase push notifications
    
    Args:
        recipients: List or QuerySet of User objects
        title: Title of the notification
        message: Message content of the notification
        notification_type: Type of notification
        related_object: Optional related object
    """
    notifications = []
    for recipient in recipients:
        notification_data = {
            'recipient': recipient,
            'title': title,
            'message': message,
            'notification_type': notification_type
        }
        
        if related_object:
            notification_data['related_object_id'] = related_object.id
            notification_data['related_object_type'] = related_object.__class__.__name__
        
        notifications.append(Notification(**notification_data))
    
    # Create all in-app notifications
    created_notifications = Notification.objects.bulk_create(notifications)
    
    # Try to send Firebase push notifications
    try:
        from .fcm_utils import send_push_notification_to_users
        
        # Prepare data for Firebase
        fcm_data = {
            'type': notification_type,
        }
        
        if related_object:
            fcm_data['related_object_id'] = str(related_object.id)
            fcm_data['related_object_type'] = related_object.__class__.__name__
        
        # Send Firebase push notifications to all recipients
        send_push_notification_to_users(
            users=recipients,
            title=title,
            body=message,
            data=fcm_data
        )
    except Exception as e:
        # If Firebase fails, log it but don't fail the notification creation
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Could not send Firebase push notifications: {e}")
    
    return created_notifications

def mark_notification_as_read(notification_id, user):
    """
    Mark a notification as read for a specific user
    
    Args:
        notification_id: ID of the notification
        user: User object who owns the notification
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False

def mark_all_notifications_as_read(user):
    """
    Mark all notifications as read for a specific user
    
    Args:
        user: User object
    """
    return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)