// Firebase Cloud Messaging initialization
// Firebase configuration - Replace with your actual Firebase config
// TODO: Update these values with your Firebase project configuration
const firebaseConfig = {
    apiKey: "AIzaSyC_00jdAaoy8YuwhD6vqwc2bK55PZ_eouY",
    authDomain: "guestconnect2.firebaseapp.com",
    projectId: "guestconnect2",
    storageBucket: "guestconnect2.firebasestorage.app",
    messagingSenderId: "1059307478512",
    appId: "1:1059307478512:web:836d6a30116854271bd135",
    measurementId: "G-080L2D262S"
};

// VAPID key from environment
const VAPID_KEY = "{{ FIREBASE_VAPID_KEY }}";

let messaging = null;

// Initialize Firebase
function initializeFirebase() {
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
    }
    messaging = firebase.messaging();
    console.log('[Firebase] Initialized successfully');
}

// Request notification permission and get FCM token
async function requestNotificationPermission() {
    try {
        const permission = await Notification.requestPermission();

        if (permission === 'granted') {
            console.log('[FCM] Notification permission granted');

            // Get FCM token
            const token = await messaging.getToken({
                vapidKey: VAPID_KEY
            });

            if (token) {
                console.log('[FCM] Token received:', token);

                // Save token to backend
                await saveFCMToken(token);

                return token;
            } else {
                console.log('[FCM] No registration token available');
            }
        } else if (permission === 'denied') {
            console.log('[FCM] Notification permission denied');
        } else {
            console.log('[FCM] Notification permission dismissed');
        }
    } catch (error) {
        console.error('[FCM] Error getting permission or token:', error);
    }
}

// Save FCM token to backend
async function saveFCMToken(token) {
    try {
        const response = await fetch('/api/save-fcm-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ token: token })
        });

        if (response.ok) {
            console.log('[FCM] Token saved to backend successfully');
        } else {
            console.error('[FCM] Failed to save token to backend');
        }
    } catch (error) {
        console.error('[FCM] Error saving token:', error);
    }
}

// Handle foreground messages
function handleForegroundMessages() {
    messaging.onMessage((payload) => {
        console.log('[FCM] Foreground message received:', payload);

        const notificationTitle = payload.notification.title || 'GuestConnect';
        const notificationOptions = {
            body: payload.notification.body || 'You have a new notification',
            icon: '/static/images/icon-192.png',
            badge: '/static/images/icon-192.png',
            vibrate: [200, 100, 200],
            data: payload.data
        };

        // Show notification
        if (Notification.permission === 'granted') {
            new Notification(notificationTitle, notificationOptions);
        }

        // You can also update UI here if needed
        displayNotificationInUI(payload);
    });
}

// Display notification in UI (optional - customize as needed)
function displayNotificationInUI(payload) {
    // Create a toast or notification element in your UI
    const notificationDiv = document.createElement('div');
    notificationDiv.className = 'fcm-notification';
    notificationDiv.innerHTML = `
    <div class="bg-blue-500 text-white px-4 py-3 rounded-lg shadow-lg mb-2">
      <h4 class="font-bold">${payload.notification.title || 'Notification'}</h4>
      <p class="text-sm">${payload.notification.body || ''}</p>
    </div>
  `;

    // Add to notification container (create if doesn't exist)
    let notificationContainer = document.getElementById('fcm-notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'fcm-notification-container';
        notificationContainer.className = 'fixed top-4 right-4 z-50 max-w-sm';
        document.body.appendChild(notificationContainer);
    }

    notificationContainer.appendChild(notificationDiv);

    // Remove after 5 seconds
    setTimeout(() => {
        notificationDiv.remove();
    }, 5000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        initializeFirebase();
        handleForegroundMessages();

        // Add a button or auto-request on first visit
        // For now, we'll add a global function that can be called from UI
        window.enableNotifications = requestNotificationPermission;

        console.log('[FCM] Ready. Call window.enableNotifications() to request permission.');
    } else {
        console.warn('[FCM] Push notifications not supported');
    }
});
