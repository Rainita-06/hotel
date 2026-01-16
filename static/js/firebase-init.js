// Firebase Cloud Messaging initialization
// Firebase configuration - GuestConnect Firebase project
const firebaseConfig = {
    apiKey: "AIzaSyC_00jdAaoy8YuwhD6vqwc2bK55PZ_eouY",
    authDomain: "guestconnect2.firebaseapp.com",
    projectId: "guestconnect2",
    storageBucket: "guestconnect2.firebasestorage.app",
    messagingSenderId: "1059307478512",
    appId: "1:1059307478512:web:836d6a30116854271bd135",
    measurementId: "G-080L2D262S"
};

// VAPID key for FCM - This should be set from the Django template or fallback to hardcoded value
const VAPID_KEY = window.FIREBASE_VAPID_KEY || "BEYA1eUQj0p-jbNICerO-xDiLkzh2SmGfreimhXk5S_bMKDHyyZJoBki2bDnNo237eY5XlYpHRdbPQLzwqPNfyo";

let messaging = null;
let swRegistration = null;

// Initialize Firebase
function initializeFirebase() {
    if (!firebase.apps.length) {
        firebase.initializeApp(firebaseConfig);
    }
    messaging = firebase.messaging();
    console.log('[Firebase] Initialized successfully');
}

// Register service worker for Firebase
async function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) {
        console.warn('[FCM] Service workers not supported');
        return null;
    }

    try {
        // Check if we're in standalone mode (PWA installed)
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone ||
            document.referrer.includes('android-app://');

        if (isStandalone) {
            console.log('[FCM] Running in PWA standalone mode');
        }

        // Use the main service worker (sw.js) which now includes Firebase logic
        // This avoids conflicts between multiple service workers on the same scope
        swRegistration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/',
            updateViaCache: 'none' // Always check for updates on Android
        });

        console.log('[FCM] Service worker registered:', swRegistration.scope);

        // Wait for the service worker to be active
        if (swRegistration.installing) {
            console.log('[FCM] Service worker installing...');
        } else if (swRegistration.waiting) {
            console.log('[FCM] Service worker waiting...');
        } else if (swRegistration.active) {
            console.log('[FCM] Service worker active');
        }

        // Check for updates on Android PWA
        if (isStandalone) {
            swRegistration.update();
        }

        return swRegistration;
    } catch (error) {
        console.error('[FCM] Service worker registration failed:', error);
        return null;
    }
}

// Request notification permission and get FCM token
async function requestNotificationPermission() {
    try {
        // First check if notifications are supported
        if (!('Notification' in window)) {
            console.log('[FCM] Notifications not supported');
            showNotificationStatus('Notifications are not supported in this browser', 'error');
            return null;
        }

        // Check if we're running as a PWA
        const isPWA = window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone ||
            document.referrer.includes('android-app://');

        if (isPWA) {
            console.log('[FCM] Running as installed PWA - notifications should work!');
        }

        // Check if we're on localhost - FCM push doesn't work on localhost
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.warn('[FCM] Push notifications require HTTPS. Use ngrok or deploy to test FCM.');
            showNotificationStatus('Push requires HTTPS. Use your ngrok URL to test.', 'warning');
            // Still allow permission request for testing
        }

        const permission = await Notification.requestPermission();

        if (permission === 'granted') {
            console.log('[FCM] Notification permission granted');
            showNotificationStatus('Notification permission granted!', 'success');

            // Ensure service worker is registered
            if (!swRegistration) {
                await registerServiceWorker();
            }

            // Wait for service worker to be ready
            if (swRegistration) {
                await navigator.serviceWorker.ready;
                console.log('[FCM] Service worker is ready');
            }

            try {
                // Get FCM token
                const token = await messaging.getToken({
                    vapidKey: VAPID_KEY,
                    serviceWorkerRegistration: swRegistration
                });

                if (token) {
                    console.log('[FCM] Token received:', token.substring(0, 20) + '...');
                    showNotificationStatus('Push notifications enabled!', 'success');

                    // Save token to backend
                    await saveFCMToken(token);

                    return token;
                } else {
                    console.log('[FCM] No registration token available');
                    showNotificationStatus('Could not get notification token', 'error');
                }
            } catch (tokenError) {
                console.error('[FCM] Token registration error:', tokenError);

                // Provide specific guidance based on error
                let errorMsg = tokenError.message || 'Unknown error';
                if (errorMsg.includes('push service error')) {
                    errorMsg = 'Push service error. Please ensure:\n1. You are using HTTPS (use ngrok URL)\n2. VAPID key matches your Firebase project';
                    console.error('[FCM] VAPID Key issue. Please verify your VAPID key in Firebase Console > Project Settings > Cloud Messaging > Web Push certificates');
                }

                showNotificationStatus(errorMsg, 'error');
            }
        } else if (permission === 'denied') {
            console.log('[FCM] Notification permission denied');
            showNotificationStatus('Notification permission was denied', 'error');
        } else {
            console.log('[FCM] Notification permission dismissed');
            showNotificationStatus('Notification permission was dismissed', 'warning');
        }
    } catch (error) {
        console.error('[FCM] Error getting permission or token:', error);
        showNotificationStatus('Error enabling notifications: ' + error.message, 'error');
    }
    return null;
}

// Save FCM token to backend
async function saveFCMToken(token) {
    try {
        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
            window.csrftoken ||
            getCookie('csrftoken');

        if (!csrfToken) {
            console.error('[FCM] No CSRF token found');
            return false;
        }

        // Detect if running as installed PWA on Android
        const isAndroidPWA = window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone ||
            /android/i.test(navigator.userAgent);
        
        const deviceType = isAndroidPWA ? 'android' : 'web';
        
        const response = await fetch('/api/notification/save-fcm-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                token: token,
                device_type: deviceType
            })
        });

        if (response.ok) {
            console.log('[FCM] Token saved to backend successfully');
            return true;
        } else {
            console.error('[FCM] Failed to save token to backend:', response.status);
            return false;
        }
    } catch (error) {
        console.error('[FCM] Error saving token:', error);
        return false;
    }
}

// Helper function to get cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Show notification status to user
function showNotificationStatus(message, type = 'info') {
    // Try to use the global showToast function if available
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
        return;
    }

    // Fallback: Create a simple notification UI
    let statusContainer = document.getElementById('fcm-status-container');
    if (!statusContainer) {
        statusContainer = document.createElement('div');
        statusContainer.id = 'fcm-status-container';
        statusContainer.className = 'fixed top-4 right-4 z-[9999] max-w-sm';
        document.body.appendChild(statusContainer);
    }

    const statusDiv = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-600' :
        type === 'error' ? 'bg-red-600' :
            type === 'warning' ? 'bg-yellow-600' : 'bg-blue-600';

    statusDiv.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg mb-2 animate-pulse`;
    statusDiv.textContent = message;
    statusContainer.appendChild(statusDiv);

    // Remove after 4 seconds
    setTimeout(() => {
        statusDiv.style.opacity = '0';
        statusDiv.style.transition = 'opacity 0.3s';
        setTimeout(() => statusDiv.remove(), 300);
    }, 4000);
}

// Set up token refresh handling
function setupTokenRefresh() {
    if (!messaging) return;

    // Listen for token refresh
    messaging.onTokenRefresh(async () => {
        console.log('[FCM] Token refresh detected');
        try {
            const newToken = await messaging.getToken({
                vapidKey: VAPID_KEY,
                serviceWorkerRegistration: swRegistration
            });

            if (newToken) {
                console.log('[FCM] New token obtained:', newToken.substring(0, 20) + '...');
                await saveFCMToken(newToken);
            }
        } catch (error) {
            console.error('[FCM] Token refresh failed:', error);
        }
    });
}

// Handle foreground messages
function handleForegroundMessages() {
    if (!messaging) return;

    messaging.onMessage((payload) => {
        console.log('[FCM] Foreground message received:', payload);

        const notificationData = payload.notification || {};
        const customData = payload.data || {};

        const notificationTitle = notificationData.title || customData.title || 'GuestConnect';
        const notificationBody = notificationData.body || customData.body || 'You have a new notification';

        // Show system notification if permission granted
        if (Notification.permission === 'granted') {
            const notificationOptions = {
                body: notificationBody,
                icon: customData.icon || '/static/images/icon-192.png',
                badge: '/static/images/icon-192.png',
                vibrate: [200, 100, 200, 100, 200],
                data: customData,
                tag: customData.tag || 'guestconnect-' + Date.now(),
                requireInteraction: true, // Important for Android
                renotify: true,
                silent: false,
                timestamp: Date.now()
            };

            const notification = new Notification(notificationTitle, notificationOptions);

            // Handle notification click in foreground
            notification.onclick = function (event) {
                event.preventDefault();
                const url = customData.url || customData.link || '/dashboard/';
                window.focus();
                window.location.href = url;
                notification.close();
            };
        }

        // Also display in UI
        displayNotificationInUI(payload);
    });
}

// Display notification in UI (toast-style)
function displayNotificationInUI(payload) {
    const title = payload.notification?.title || 'Notification';
    const body = payload.notification?.body || '';

    // Try to use showToast if available
    if (typeof window.showToast === 'function') {
        window.showToast(`${title}: ${body}`, 'info');
        return;
    }

    // Fallback notification display
    let notificationContainer = document.getElementById('fcm-notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'fcm-notification-container';
        notificationContainer.className = 'fixed top-4 right-4 z-[9999] max-w-sm';
        document.body.appendChild(notificationContainer);
    }

    const notificationDiv = document.createElement('div');
    notificationDiv.className = 'bg-sky-600 text-white px-4 py-3 rounded-lg shadow-lg mb-2';
    notificationDiv.innerHTML = `
        <div class="font-bold text-sm">${title}</div>
        <div class="text-sm opacity-90">${body}</div>
    `;

    notificationContainer.appendChild(notificationDiv);

    // Remove after 5 seconds
    setTimeout(() => {
        notificationDiv.style.opacity = '0';
        notificationDiv.style.transition = 'opacity 0.3s';
        setTimeout(() => notificationDiv.remove(), 300);
    }, 5000);
}

// Check notification status
function checkNotificationStatus() {
    if (!('Notification' in window)) {
        return 'unsupported';
    }
    return Notification.permission;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
            // Initialize Firebase
            initializeFirebase();

            // Register service worker
            await registerServiceWorker();

            // Set up foreground message handling
            handleForegroundMessages();

            // Expose functions globally
            window.enableNotifications = requestNotificationPermission;
            window.checkNotificationStatus = checkNotificationStatus;

            console.log('[FCM] Ready. Call window.enableNotifications() to request permission.');
            console.log('[FCM] Current permission status:', checkNotificationStatus());

            // Auto-request if already granted (to get fresh token)
            if (Notification.permission === 'granted') {
                console.log('[FCM] Notifications already granted, getting token...');
                requestNotificationPermission();
            }

            // Set up token refresh
            setupTokenRefresh();
        } catch (error) {
            console.error('[FCM] Initialization error:', error);
        }
    } else {
        console.warn('[FCM] Push notifications not supported in this browser');
    }
});
