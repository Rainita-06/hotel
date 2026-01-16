# Push Notification Setup Guide

## Overview
This guide explains how to properly configure push notifications for the GuestConnect PWA application.

## Prerequisites
1. Firebase project created in Firebase Console
2. Firebase Admin SDK service account key
3. Proper VAPID key configured
4. Application served over HTTPS (required for production)

## Steps to Enable Push Notifications

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing one
3. Navigate to Project Settings > General
4. Add your web app if not already added

### 2. Generate Service Account Key
1. In Firebase Console, go to Project Settings > Service Accounts
2. Click "Generate new private key" for Firebase Admin SDK
3. Download the JSON file
4. Rename it to `firebase-service-account.json`
5. Replace the placeholder file in the project root directory with the actual key
6. Add it to `.gitignore` (already configured in your project)

### 3. Configure VAPID Key
1. In Firebase Console, go to Project Settings > Cloud Messaging
2. Under "Web Push certificates", click "Generate key pair" if you don't have one
3. Copy the "Public key" 
4. Update the VAPID key in your Django settings if needed

### 4. Update Firebase Configuration
1. Make sure the Firebase configuration in:
   - `static/js/firebase-init.js`
   - `static/sw.js`
   - `static/firebase-messaging-sw.js`
   
   matches your Firebase project configuration

### 5. Deploy Over HTTPS
- Push notifications require HTTPS in production environments
- For development/testing over HTTP, use localhost or tools like ngrok
- Android PWA will only receive push notifications when served over HTTPS

### 6. Android PWA Specific Considerations
- The app automatically detects when it's running as an installed PWA on Android
- Device type is automatically set to 'android' when running as PWA
- Android-specific notification options are applied (requireInteraction: true)
- The service worker is optimized for Android Chrome

## Troubleshooting

### Common Issues
1. **No notifications appearing**: Check if the real `firebase-service-account.json` file exists (not the placeholder)
2. **Notifications only work in foreground**: Ensure service worker is properly registered
3. **Android PWA not receiving notifications**: Verify the app is served over HTTPS
4. **FCM tokens not saving**: Check that the API endpoint `/api/notification/save-fcm-token/` is accessible
5. **Duplicate service workers**: Ensure only one service worker is registered (should be fixed in latest version)

### Debugging Tips
1. Open browser DevTools > Application > Service Workers to verify only ONE service worker is registered
2. Check DevTools > Console for Firebase initialization errors
3. Verify FCM tokens are being saved with correct device_type in the database
4. Check browser notification permissions are granted
5. Look for network errors when calling `/api/notification/save-fcm-token/`
6. Ensure the app is served over HTTPS in production

## Security Notes
- Never commit `firebase-service-account.json` to version control
- The file is already in `.gitignore`
- Keep your VAPID keys secure
- Use environment variables for sensitive configuration in production