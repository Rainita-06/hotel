// Firebase Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

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

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Retrieve an instance of Firebase Messaging
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Received background message ', payload);

    const notificationTitle = payload.notification.title || 'GuestConnect Notification';
    const notificationOptions = {
        body: payload.notification.body || 'You have a new notification',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        vibrate: [200, 100, 200],
        data: payload.data,
        actions: [
            {
                action: 'open',
                title: 'Open App'
            },
            {
                action: 'close',
                title: 'Close'
            }
        ]
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Notification clicked', event);

    event.notification.close();

    if (event.action === 'open' || !event.action) {
        // Open the app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});
