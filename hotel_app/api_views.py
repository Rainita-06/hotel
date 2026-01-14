from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Notification, FCMToken
from .serializers import NotificationSerializer
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.contrib.auth import get_user_model

User = get_user_model()


@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def current_user(request):
    """API endpoint to check if user is authenticated and get user info."""
    user = request.user
    return Response({
        'is_authenticated': True,
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
    })

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """
    Get unread notifications for the current user
    """
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_all_notifications(request):
    """
    Get all notifications for the current user
    """
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    """
    Mark a specific notification as read
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.mark_as_read()
    return Response({'status': 'success'})

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def mark_all_notifications_as_read(request):
    """
    Mark all notifications as read for the current user
    """
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({'status': 'success'})

@api_view(['DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_notification(request, notification_id):
    """
    Delete a specific notification
    """
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )
    
    notification.delete()
    return Response({'status': 'success'})


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_fcm_token(request):
    """
    Save Firebase Cloud Messaging token for the current user
    """
    token = request.data.get('token')
    device_type = request.data.get('device_type', 'web')
    
    if not token:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create the FCM token for this user
    fcm_token, created = FCMToken.objects.get_or_create(
        token=token,
        defaults={
            'user': request.user,
            'device_type': device_type,
            'is_active': True
        }
    )
    
    # If token already exists but for a different user, update it
    if not created and fcm_token.user != request.user:
        fcm_token.user = request.user
        fcm_token.save()
    
    # Reactivate if it was deactivated
    if not fcm_token.is_active:
        fcm_token.is_active = True
        fcm_token.save(update_fields=['is_active'])
    
    # Mark as used
    fcm_token.mark_as_used()
    
    return Response({
        'status': 'success',
        'message': 'FCM token saved successfully',
        'created': created
    })


@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_fcm_token(request):
    """
    Delete/deactivate Firebase Cloud Messaging token for the current user
    """
    token = request.data.get('token')
    
    if not token:
        return Response(
            {'error': 'Token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        fcm_token = FCMToken.objects.get(
            token=token,
            user=request.user
        )
        fcm_token.deactivate()
        return Response({
            'status': 'success',
            'message': 'FCM token deactivated successfully'
        })
    except FCMToken.DoesNotExist:
        return Response(
            {'error': 'Token not found'},
            status=status.HTTP_404_NOT_FOUND
        )
