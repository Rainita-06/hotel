# Testing Push Notifications

## Pre-requisites Checklist

Before testing push notifications on your Android PWA, ensure all of these are met:

1. ✅ **Single Service Worker Registration**: Only `/sw.js` should be registered (not both `sw.js` and `firebase-messaging-sw.js`)
2. ✅ **Real Firebase Credentials**: `firebase-service-account.json` contains actual Firebase service account key (not placeholder)
3. ✅ **HTTPS Deployment**: App is served over HTTPS in production (localhost is OK for development)
4. ✅ **FCM Token Saved**: Device shows FCM token is registered with `device_type: 'android'` in database
5. ✅ **Notification Permissions**: Granted in browser/PWA

## How to Test Push Notifications

### 1. Check FCM Token Registration
1. Open your PWA on Android
2. Check browser console for FCM token registration messages
3. Verify token is saved in database with `device_type = 'android'`:
   ```bash
   python manage.py shell
   from hotel_app.models import FCMToken
   print(FCMToken.objects.all())
   ```

### 2. Test Manual Notification
Create a test notification to verify the system works:
```bash
python manage.py create_test_notification
```

### 3. Check Service Worker Status
1. Open Chrome DevTools on Android
2. Go to Application > Service Workers
3. Verify only ONE service worker is registered (`sw.js`)
4. Check for any errors in the console

### 4. Simulate Notification Trigger
You can manually trigger a notification using:
```bash
python manage.py shell
from hotel_app.utils import create_notification
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()  # Or select specific user

notification = create_notification(
    recipient=user,
    title="Test Push Notification",
    message="This is a test to verify push notifications work",
    notification_type="test"
)
print("Notification created and push sent!")
```

### 5. Monitor Network Requests
In browser dev tools:
1. Check Network tab for successful POST to `/api/notification/save-fcm-token/`
2. Verify no errors when requesting notification permission
3. Look for successful FCM token retrieval

## Common Android-Specific Issues

1. **Background App Killing**: Android aggressively kills background PWA apps, which may unregister service workers
2. **Battery Optimization**: Some Android devices put PWAs in battery optimization which affects push delivery
3. **Chrome Version**: Older Chrome versions may not support all FCM features
4. **Notification Channel**: Android Oreo+ requires notification channels (handled by our service worker)

## Debugging Steps

If notifications still don't appear on Android:

1. **Check Android PWA Installation**:
   - Ensure app was properly installed as PWA from Chrome menu > "Install app"
   - Verify it appears in Android app drawer

2. **Verify Device Type Detection**:
   - In console, check if `isAndroidPWA` evaluates to `true`
   - Check database if token has `device_type = 'android'`

3. **Check Service Worker Scope**:
   - Ensure service worker has correct scope (`/`)
   - Verify it's not being blocked by CSP policies

4. **Review Firebase Console**:
   - Check Firebase Console > Cloud Messaging for any delivery issues
   - Verify FCM server key matches client-side configuration

## Expected Behavior

- When notification is triggered server-side → Firebase sends to FCM token → Service worker receives → Shows on Android device
- Both foreground and background notifications should work
- Clicking notification should open the app

## Production Deployment Notes

For production deployment, ensure:
- SSL certificate is valid
- Domain matches Firebase project configuration
- Server time is synchronized (important for Firebase authentication)
- Proper CORS headers for API requests