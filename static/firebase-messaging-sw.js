// Firebase Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

// Firebase configuration - Replace with your actual Firebase config
// TODO: Update these values with your Firebase project configuration
const firebaseConfig = {
    apiKey: "AIzaSyCfgY8622WSb-iYlTip2M02tPGwRJzQltM",
  authDomain: "guestconnect2-341a2.firebaseapp.com",
  projectId: "guestconnect2-341a2",
  storageBucket: "guestconnect2-341a2.firebasestorage.app",
  messagingSenderId: "301374504112",
  appId: "1:301374504112:web:83a455ec8eb98bbc5fcf75",
  measurementId: "G-X0X2SP8BKS"

};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Retrieve an instance of Firebase Messaging
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Received background message ', payload);

    // Extract notification data with fallbacks
    const notificationData = payload.notification || {};
    const customData = payload.data || {};

    const notificationTitle = notificationData.title || customData.title || 'GuestConnect Notification';
    const notificationOptions = {
        body: notificationData.body || customData.body || 'You have a new notification',
        icon: customData.icon || '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        vibrate: [200, 100, 200, 100, 200],
        data: customData,
        tag: customData.tag || 'guestconnect-' + Date.now(),
        requireInteraction: true, // Critical for Android - keeps notification visible
        renotify: true,
        silent: false,
        actions: [
            {
                action: 'open',
                title: 'Open App',
                icon: '/static/images/icon-192.png'
            },
            {
                action: 'close',
                title: 'Dismiss'
            }
        ],
        image: customData.image || null,
        timestamp: Date.now()
    };

    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Notification clicked', event.action, event.notification.data);

    event.notification.close();

    if (event.action === 'close') {
        // User dismissed the notification
        return;
    }

    // Determine the URL to open
    const urlToOpen = new URL(
        event.notification.data?.url ||
        event.notification.data?.link ||
        '/',
        self.location.origin
    ).href;

    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        })
            .then(clientList => {
                // First, try to find an existing window with the exact URL
                for (const client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Then, try to find any window with the app
                for (const client of clientList) {
                    if ('focus' in client) {
                        // Navigate to the target URL and focus
                        return client.focus().then(() => {
                            if (client.navigate) {
                                return client.navigate(urlToOpen);
                            }
                        });
                    }
                }

                // No existing window found, open a new one
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
            .catch(error => {
                console.error('[firebase-messaging-sw.js] Error handling notification click:', error);
                // Fallback: try to open window anyway
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});
