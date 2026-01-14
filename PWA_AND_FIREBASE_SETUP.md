# Progressive Web App (PWA) & Firebase Cloud Messaging Setup

This document provides instructions for completing the Progressive Web App (PWA) setup and configuring Firebase Cloud Messaging (FCM) for push notifications.

## ✅ What's Already Done

1. **PWA Manifest** - Created at `static/manifest.json`
2. **Service Workers** - Created:
   - `static/sw.js` - Main service worker for offline capability
   - `static/firebase-messaging-sw.js` - FCM service worker for push notifications
3. **PWA Icons** - Generated and placed at:
   - `static/images/icon-192.png`
   - `static/images/icon-512.png`
4. **Base Template Updated** - `templates/base.html` now includes:
   - PWA manifest link
   - Theme color meta tags
   - Apple touch icon support
   - Firebase SDK scripts
   - Service worker registration
5. **Database Model** - `FCMToken` model created and migrated
6. **API Endpoints** - Created for saving/deleting FCM tokens:
   - `/api/save-fcm-token/` - Save FCM token
   - `/api/delete-fcm-token/` - Delete FCM token
7. **Environment Variable** - VAPID key added to `.env` file

## 🔧 What You Need to Do

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or select existing project
3. Follow the setup wizard (you can disable Google Analytics if not needed)

### Step 2: Register Web App in Firebase

1. In your Firebase project, click the **Web icon** (</>) to add a web app
2. Register your app with a nickname (e.g., "GuestConnect")
3. **Copy the Firebase configuration object** - it looks like this:

```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

### Step 3: Enable Cloud Messaging

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Navigate to the **Cloud Messaging** tab
3. Your **VAPID key** is already in the `.env` file, but verify it matches what's shown here
4. If you need to generate a new key pair, click "Generate key pair"

### Step 4: Update Firebase Configuration Files

You need to update the Firebase configuration in **TWO files**:

#### File 1: `static/firebase-messaging-sw.js`

Replace the placeholder config (lines 6-13) with your actual Firebase config:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_ACTUAL_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

#### File 2: `static/js/firebase-init.js`

Replace the placeholder config (lines 3-10) with your actual Firebase config:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_ACTUAL_API_KEY",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};
```

### Step 5: Verify VAPID Key

The VAPID key is already set in your `.env` file:
```
FIREBASE_VAPID_KEY=BNqsYcBpb2AB7IWFSJpoQt2t7Gb3zWPhFc9QjurMct-FZl6VHLixKIw2JzfSz9CltIKpO-dgNaM_QOegCx_L6vE
```

Verify this matches the key in your Firebase Console (Project Settings > Cloud Messaging > Web Push certificates).

### Step 6: Deploy to HTTPS

⚠️ **IMPORTANT**: PWAs and push notifications require HTTPS! They will NOT work on `http://localhost` in production.

**For Development:**
- PWAs work on `localhost` without HTTPS
- But for full testing, deploy to a hosting service

**Free HTTPS Hosting Options:**
- [Vercel](https://vercel.com) - Recommended for Django + static files
- [Netlify](https://netlify.com)
- [Cloudflare Pages](https://pages.cloudflare.com)
- [Railway](https://railway.app)
- [Render](https://render.com)

### Step 7: Test the PWA

1. **Run your development server:**
   ```bash
   python manage.py runserver
   ```

2. **Open Chrome DevTools:**
   - Press F12
   - Go to **Application** tab
   - Check **Manifest** section - should show your app details
   - Check **Service Workers** section - should show 2 registered workers

3. **Test Install:**
   - Look for an install button in the address bar (desktop)
   - Or in Chrome menu → "Install GuestConnect"

4. **Test Notifications:**
   - Open browser console
   - Type: `window.enableNotifications()`
   - Allow notification permission when prompted
   - Check console for FCM token

### Step 8: Send Test Notification

**Option A: Using Firebase Console**
1. Go to Firebase Console → Cloud Messaging
2. Click "Send your first message"
3. Enter title and text
4. Click "Send test message"
5. Enter the FCM token from your console
6. Click "Test"

**Option B: Using Backend (Python)**

Later you can integrate Firebase Admin SDK to send notifications from your Django backend:

```python
# Install: pip install firebase-admin

import firebase_admin
from firebase_admin import credentials, messaging

# Initialize (do this once in settings or app startup)
cred = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Send notification
def send_push_notification(user, title, body):
    # Get user's FCM tokens
    tokens = user.fcm_tokens.filter(is_active=True).values_list('token', flat=True)
    
    if not tokens:
        return
    
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        tokens=list(tokens),
    )
    
    response = messaging.send_multicast(message)
    print(f'Successfully sent {response.success_count} messages.')
```

## 🎨 Customization

### Change App Colors
Edit `static/manifest.json`:
```json
{
  "theme_color": "#0284C7",  // Blue theme
  "background_color": "#ffffff"
}
```

### Change App Name
Edit `static/manifest.json`:
```json
{
  "name": "Your Hotel Name",
  "short_name": "Hotel"
}
```

### Customize Icons
Replace the generated icons with your own:
- `static/images/icon-192.png` (192×192 pixels)
- `static/images/icon-512.png` (512×512 pixels)

## 📱 Testing on Mobile

1. Deploy your app to HTTPS
2. Open in mobile browser (Chrome/Safari)
3. Look for "Add to Home Screen" prompt
4. Install the app
5. Test notifications

## 🔍 Troubleshooting

### Service Worker Not Registering
- Check browser console for errors
- Ensure files are served from correct paths
- Clear browser cache (Ctrl+Shift+Delete)

### Notifications Not Working
- Verify Firebase config is correct in both files
- Check notification permission is granted
- Verify VAPID key matches Firebase console
- Check browser console for FCM token

### PWA Not Installable
- Must be served over HTTPS (except localhost)
- Check manifest.json is valid
- Icons must be correct size and format
- Service worker must be registered

### FCM Token Not Saving
- Check browser console for errors
- Verify API endpoint is accessible
- Check CSRF token is being sent
- Verify user is authenticated

## 📚 Resources

- [PWA Documentation](https://web.dev/progressive-web-apps/)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [Service Workers](https://developers.google.com/web/fundamentals/primers/service-workers)
- [Web App Manifest](https://web.dev/add-manifest/)

## 💰 Cost

- **PWA Hosting**: Free (with providers listed above)
- **Firebase Cloud Messaging**: FREE unlimited notifications
- **Total Cost**: ₹0

## ✅ Checklist

- [ ] Created Firebase project
- [ ] Registered web app in Firebase
- [ ] Copied Firebase config to `firebase-messaging-sw.js`
- [ ] Copied Firebase config to `firebase-init.js`
- [ ] Verified VAPID key in `.env` file
- [ ] Tested service worker registration
- [ ] Tested notification permission request
- [ ] Sent test notification
- [ ] Deployed to HTTPS
- [ ] Tested PWA installation
- [ ] Tested notifications on mobile

## 🎉 You're Done!

Your hotel management app is now a Progressive Web App with push notification support!
