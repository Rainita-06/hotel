"""
Backend Integration: Sending Push Notifications with Firebase Admin SDK

This file shows how to send push notifications from Django backend.
"""

# ==============================================================================
# STEP 1: Install Firebase Admin SDK
# ==============================================================================
# pip install firebase-admin

# ==============================================================================
# STEP 2: Get Service Account Key from Firebase
# ==============================================================================
# 1. Go to Firebase Console → Project Settings → Service Accounts
# 2. Click "Generate new private key"
# 3. Save the JSON file as 'firebase-service-account.json' in your project root
# 4. Add to .gitignore to keep it secure!

# ==============================================================================
# STEP 3: Initialize Firebase Admin (One-time setup)
# ==============================================================================
# Add this to your Django settings.py or apps.py

import firebase_admin
from firebase_admin import credentials
from pathlib import Path
import os

# Initialize Firebase Admin SDK (do this once)
BASE_DIR = Path(__file__).resolve().parent.parent
cred = credentials.Certificate(os.path.join(BASE_DIR, 'firebase-service-account.json'))

# Check if already initialized to avoid errors
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)


# ==============================================================================
# STEP 4: Create Notification Utility Function
# ==============================================================================
# Add this to hotel_app/utils.py or create a new file: hotel_app/fcm_utils.py

from firebase_admin import messaging
from hotel_app.models import FCMToken
from django.contrib.auth import get_user_model

User = get_user_model()


def send_push_notification_to_user(user, title, body, data=None):
    """
    Send push notification to a specific user.
    
    Args:
        user: User object
        title: Notification title
        body: Notification body/message
        data: Optional dict of custom data to send with notification
    
    Returns:
        dict: Response with success count and failed token IDs
    """
    # Get all active FCM tokens for this user
    tokens = list(
        FCMToken.objects.filter(user=user, is_active=True)
        .values_list('token', flat=True)
    )
    
    if not tokens:
        print(f"No active FCM tokens found for user: {user.username}")
        return {'success_count': 0, 'failure_count': 0}
    
    # Create notification message
    notification = messaging.Notification(
        title=title,
        body=body,
    )
    
    # Create multicast message
    message = messaging.MulticastMessage(
        notification=notification,
        data=data or {},
        tokens=tokens,
    )
    
    try:
        # Send notification
        response = messaging.send_multicast(message)
        
        # Handle failed tokens (deactivate them)
        if response.failure_count > 0:
            failed_tokens = [
                tokens[idx] 
                for idx, resp in enumerate(response.responses) 
                if not resp.success
            ]
            # Deactivate failed tokens
            FCMToken.objects.filter(token__in=failed_tokens).update(is_active=False)
        
        print(f'Successfully sent {response.success_count} notifications to {user.username}')
        print(f'Failed to send {response.failure_count} notifications')
        
        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count,
            'failed_tokens': failed_tokens if response.failure_count > 0 else []
        }
        
    except Exception as e:
        print(f'Error sending notification: {e}')
        return {'success_count': 0, 'failure_count': len(tokens), 'error': str(e)}


def send_push_notification_to_users(users, title, body, data=None):
    """
    Send push notification to multiple users.
    
    Args:
        users: QuerySet or list of User objects
        title: Notification title
        body: Notification body/message
        data: Optional dict of custom data
    
    Returns:
        dict: Aggregated response with total success/failure counts
    """
    total_success = 0
    total_failure = 0
    
    for user in users:
        result = send_push_notification_to_user(user, title, body, data)
        total_success += result['success_count']
        total_failure += result['failure_count']
    
    return {
        'total_success': total_success,
        'total_failure': total_failure,
        'users_notified': users.count() if hasattr(users, 'count') else len(users)
    }


def send_push_notification_to_department(department, title, body, data=None):
    """
    Send push notification to all users in a department.
    
    Args:
        department: Department object
        title: Notification title
        body: Notification body/message
        data: Optional dict of custom data
    """
    users = User.objects.filter(userprofile__department=department)
    return send_push_notification_to_users(users, title, body, data)


# ==============================================================================
# STEP 5: Integration Examples
# ==============================================================================

# Example 1: Send notification when a new ticket is created
# In hotel_app/views.py or wherever you create tickets

def create_service_request(request):
    # ... your ticket creation logic ...
    
    # Send notification to department staff
    if ticket.department:
        send_push_notification_to_department(
            department=ticket.department,
            title=f"New Ticket #{ticket.pk}",
            body=f"New {ticket.request_type.name} request from Room {ticket.room_no}",
            data={
                'ticket_id': str(ticket.pk),
                'type': 'new_ticket',
                'url': f'/dashboard/tickets/{ticket.pk}/'
            }
        )
    
    # Send notification to assigned user
    if ticket.assignee_user:
        send_push_notification_to_user(
            user=ticket.assignee_user,
            title=f"Ticket Assigned: #{ticket.pk}",
            body=f"You have been assigned a new {ticket.request_type.name} ticket",
            data={
                'ticket_id': str(ticket.pk),
                'type': 'ticket_assigned',
                'url': f'/dashboard/tickets/{ticket.pk}/'
            }
        )


# Example 2: Send notification when ticket is completed
def complete_ticket(request, ticket_id):
    ticket = ServiceRequest.objects.get(pk=ticket_id)
    ticket.complete_task()
    
    # Notify requester
    if ticket.requester_user:
        send_push_notification_to_user(
            user=ticket.requester_user,
            title=f"Ticket Completed: #{ticket.pk}",
            body=f"Your {ticket.request_type.name} request has been completed!",
            data={
                'ticket_id': str(ticket.pk),
                'type': 'ticket_completed',
                'url': f'/dashboard/tickets/{ticket.pk}/'
            }
        )


# Example 3: Send notification for SLA breach
def check_sla_breaches():
    """Run this as a scheduled task (e.g., with Celery or Django-Cron)"""
    from django.utils import timezone
    
    # Get tickets approaching SLA deadline
    breached_tickets = ServiceRequest.objects.filter(
        status__in=['pending', 'in_progress'],
        due_at__lte=timezone.now(),
        sla_breached=False
    )
    
    for ticket in breached_tickets:
        # Mark as breached
        ticket.sla_breached = True
        ticket.save()
        
        # Notify assigned user
        if ticket.assignee_user:
            send_push_notification_to_user(
                user=ticket.assignee_user,
                title=f"⚠️ SLA Breach: Ticket #{ticket.pk}",
                body=f"Ticket #{ticket.pk} has breached its SLA deadline!",
                data={
                    'ticket_id': str(ticket.pk),
                    'type': 'sla_breach',
                    'priority': 'high',
                    'url': f'/dashboard/tickets/{ticket.pk}/'
                }
            )


# Example 4: Send notification for new review
def create_review(request):
    # ... review creation logic ...
    
    # Notify all admins
    admins = User.objects.filter(is_superuser=True)
    send_push_notification_to_users(
        users=admins,
        title="New Guest Review",
        body=f"{review.guest_name} left a {review.rating}⭐ review",
        data={
            'review_id': str(review.pk),
            'type': 'new_review',
            'rating': str(review.rating),
            'url': '/dashboard/reviews/'
        }
    )


# Example 5: Send notification for lost & found item
def broadcast_lost_item(lost_item):
    """Send notification to all staff about lost item"""
    all_staff = User.objects.filter(is_staff=True, is_active=True)
    
    send_push_notification_to_users(
        users=all_staff,
        title=f"Lost Item Alert: {lost_item.item_name}",
        body=f"Guest from Room {lost_item.room_number} reported a lost {lost_item.item_name}",
        data={
            'item_id': str(lost_item.pk),
            'type': 'lost_item',
            'url': f'/dashboard/lost-and-found/{lost_item.pk}/'
        }
    )


# ==============================================================================
# STEP 6: Advanced Features
# ==============================================================================

def send_scheduled_notification(user, title, body, send_at):
    """
    Schedule a notification to be sent at a specific time.
    Requires Celery or similar task queue.
    """
    # This is a placeholder - implement with Celery
    from celery import shared_task
    from datetime import datetime
    
    @shared_task
    def delayed_notification():
        send_push_notification_to_user(user, title, body)
    
    # Schedule the task
    eta = datetime.fromisoformat(send_at)
    delayed_notification.apply_async(eta=eta)


def send_notification_with_action_buttons(user, title, body):
    """Send notification with action buttons"""
    tokens = list(
        FCMToken.objects.filter(user=user, is_active=True)
        .values_list('token', flat=True)
    )
    
    if not tokens:
        return
    
    # Create notification with action buttons
    notification = messaging.Notification(title=title, body=body)
    
    # Web push config with action buttons
    webpush_config = messaging.WebpushConfig(
        notification=messaging.WebpushNotification(
            title=title,
            body=body,
            icon='/static/images/icon-192.png',
            actions=[
                messaging.WebpushNotificationAction(
                    action='view',
                    title='View'
                ),
                messaging.WebpushNotificationAction(
                    action='dismiss',
                    title='Dismiss'
                ),
            ]
        )
    )
    
    message = messaging.MulticastMessage(
        notification=notification,
        webpush=webpush_config,
        tokens=tokens,
    )
    
    response = messaging.send_multicast(message)
    return response


# ==============================================================================
# USAGE IN YOUR VIEWS
# ==============================================================================

"""
Just import the function and call it:

from hotel_app.fcm_utils import send_push_notification_to_user

# Somewhere in your view/signal/etc
send_push_notification_to_user(
    user=request.user,
    title="Hello!",
    body="This is a test notification",
    data={'key': 'value'}
)
"""

# ==============================================================================
# TESTING
# ==============================================================================

def test_notification(request):
    """Test endpoint - call this to test notifications"""
    send_push_notification_to_user(
        user=request.user,
        title="Test Notification",
        body="This is a test push notification from GuestConnect!",
        data={
            'test': 'true',
            'timestamp': str(timezone.now())
        }
    )
    return JsonResponse({'status': 'Notification sent!'})
