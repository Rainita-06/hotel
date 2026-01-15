"""
Firebase Cloud Messaging Utility Functions
==========================================

This module provides functions to send push notifications via Firebase.

SETUP REQUIRED:
1. pip install firebase-admin
2. Download service account key from Firebase Console
3. Save as 'firebase-service-account.json' in project root
4. Add to .gitignore!
"""

import logging
from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

# Flag to check if Firebase Admin SDK is available
FIREBASE_AVAILABLE = False
messaging = None

try:
    import firebase_admin
    from firebase_admin import credentials, messaging as fcm_messaging
    from pathlib import Path
    import os
    
    # Try to initialize Firebase Admin SDK
    BASE_DIR = Path(__file__).resolve().parent.parent
    service_account_path = os.path.join(BASE_DIR, 'firebase-service-account.json')
    
    if os.path.exists(service_account_path):
        # Initialize only if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            messaging = fcm_messaging
            FIREBASE_AVAILABLE = True
            logger.info("Firebase Admin SDK initialized successfully")
        else:
            messaging = fcm_messaging
            FIREBASE_AVAILABLE = True
    else:
        logger.warning(
            f"Firebase service account key not found at: {service_account_path}\n"
            "Push notifications will not be sent. To enable:\n"
            "1. Download service account key from Firebase Console\n"
            "2. Save as 'firebase-service-account.json' in project root"
        )
except ImportError:
    logger.warning(
        "firebase-admin package not installed. Push notifications disabled.\n"
        "To enable: pip install firebase-admin"
    )


def send_push_notification_to_user(
    user: User,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Send push notification to a specific user.
    
    Args:
        user: User object to send notification to
        title: Notification title
        body: Notification body/message
        data: Optional dictionary of custom data (all values must be strings)
    
    Returns:
        dict: Response with success count and failure count
    """
    if not FIREBASE_AVAILABLE:
        logger.debug(f"Firebase not available. Skipping push notification to {user.username}")
        return {'success_count': 0, 'failure_count': 0, 'error': 'Firebase not configured'}
    
    # Import here to avoid errors if model doesn't exist yet
    try:
        from hotel_app.models import FCMToken
    except ImportError:
        return {'success_count': 0, 'failure_count': 0, 'error': 'FCMToken model not available'}
    
    # Get all active FCM tokens for this user
    tokens = list(
        FCMToken.objects.filter(user=user, is_active=True)
        .values_list('token', flat=True)
    )
    
    if not tokens:
        logger.debug(f"No active FCM tokens found for user: {user.username}")
        return {'success_count': 0, 'failure_count': 0, 'error': 'No FCM tokens'}
    
    # Ensure all data values are strings
    if data:
        data = {k: str(v) for k, v in data.items()}
    
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
            logger.warning(f"Deactivated {len(failed_tokens)} invalid tokens for {user.username}")
        
        logger.info(
            f'Sent push notification to {user.username}: '
            f'{response.success_count} succeeded, {response.failure_count} failed'
        )
        
        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count,
        }
        
    except Exception as e:
        logger.error(f'Error sending push notification to {user.username}: {e}')
        return {'success_count': 0, 'failure_count': len(tokens), 'error': str(e)}


def send_push_notification_to_users(
    users: List[User],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Send push notification to multiple users.
    
    Args:
        users: List or QuerySet of User objects
        title: Notification title
        body: Notification body/message
        data: Optional dictionary of custom data
    
    Returns:
        dict: Aggregated response with total success/failure counts
    """
    total_success = 0
    total_failure = 0
    
    for user in users:
        result = send_push_notification_to_user(user, title, body, data)
        total_success += result.get('success_count', 0)
        total_failure += result.get('failure_count', 0)
    
    return {
        'total_success': total_success,
        'total_failure': total_failure,
        'users_count': len(users) if isinstance(users, list) else users.count()
    }


def send_push_notification_to_department(
    department,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Send push notification to all users in a department.
    
    Args:
        department: Department object
        title: Notification title
        body: Notification body/message
        data: Optional dictionary of custom data
    
    Returns:
        dict: Response with success/failure counts
    """
    users = User.objects.filter(userprofile__department=department, is_active=True)
    return send_push_notification_to_users(users, title, body, data)


# Backward compatibility: If Firebase is not available, these functions will just log and return
# This allows the app to work without Firebase configured
