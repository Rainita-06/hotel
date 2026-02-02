// Main Service Worker (Combined PWA + Firebase)
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

const CACHE_NAME = 'guestconnect-v2-firebase'; // Updated version
const STATIC_CACHE_NAME = 'guestconnect-static-v5';
const DYNAMIC_CACHE_NAME = 'guestconnect-dynamic-v5';

// --- FIREBASE CONFIGURATION ---
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
try {
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    // Handle background messages via Firebase
    messaging.onBackgroundMessage((payload) => {
        console.log('[sw.js] Received background message ', payload);

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
            tag: customData.tag || 'guestconnect-' + Date.now(), // Unique tag to avoid duplicates
            requireInteraction: true, // Critical for Android - keeps notification visible
            renotify: true, // Re-alert user even if tag is same
            silent: false, // Ensure sound/vibration
            actions: [
                { action: 'open', title: 'Open', icon: '/static/images/icon-192.png' },
                { action: 'close', title: 'Dismiss' }
            ],
            // Android-specific optimizations
            image: customData.image || null,
            timestamp: Date.now()
        };

        return self.registration.showNotification(notificationTitle, notificationOptions);
    });

    console.log('[sw.js] Firebase messaging initialized successfully');
} catch (error) {
    console.error('[sw.js] Firebase init error:', error);
    // Still allow service worker to function without Firebase
}

// Static assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/dashboard/',
    '/static/images/icon-192.png',
    '/static/images/icon-512.png',
    '/static/images/favicon.ico',
    '/manifest.json'
];

// Install event - cache static resources
self.addEventListener('install', event => {
    console.log('[Service Worker] Installing v2...');
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('[Service Worker] Caching static assets');
                // Cache what we can, don't fail if some resources aren't available
                return Promise.allSettled(
                    STATIC_ASSETS.map(url =>
                        cache.add(url).catch(err => {
                            console.log('[Service Worker] Failed to cache:', url, err);
                        })
                    )
                );
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[Service Worker] Activating v2...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE_NAME &&
                        cacheName !== DYNAMIC_CACHE_NAME &&
                        !cacheName.includes('firebase')) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - network first for API, cache first for static
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension, admin, and API requests
    if (url.protocol === 'chrome-extension:' ||
        url.pathname.startsWith('/admin') ||
        url.pathname.startsWith('/api/')) {
        return;
    }

    // For static assets, use cache first
    if (url.pathname.startsWith('/static/') ||
        url.pathname === '/manifest.json' ||
        url.pathname.endsWith('.png') ||
        url.pathname.endsWith('.ico')) {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetch(request).then(networkResponse => {
                        // Cache for future use
                        if (networkResponse.ok) {
                            const responseClone = networkResponse.clone();
                            caches.open(STATIC_CACHE_NAME).then(cache => {
                                cache.put(request, responseClone);
                            });
                        }
                        return networkResponse;
                    });
                })
        );
        return;
    }

    // For navigation requests (HTML pages), use network first with cache fallback
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Don't cache non-successful responses or login pages
                    if (response.ok && !url.pathname.startsWith('/login')) {
                        const responseClone = response.clone();
                        caches.open(DYNAMIC_CACHE_NAME).then(cache => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // If offline, try to serve from cache
                    return caches.match(request).then(cachedResponse => {
                        if (cachedResponse) {
                            return cachedResponse;
                        }
                        // Return a basic offline page if nothing cached
                        return caches.match('/dashboard/');
                    });
                })
        );
        return;
    }

    // For everything else, try network first
    event.respondWith(
        fetch(request)
            .catch(() => caches.match(request))
    );
});

// Handle push notifications (fallback for direct push messages)
self.addEventListener('push', event => {
    console.log('[Service Worker] Push received', event);

    let data = {};
    let notificationData = {};

    if (event.data) {
        try {
            const jsonData = event.data.json();
            data = jsonData.data || {};
            notificationData = jsonData.notification || jsonData;
        } catch (e) {
            console.log('[Service Worker] Push data not JSON:', e);
            notificationData = { title: 'Notification', body: event.data.text() };
        }
    }

    const title = notificationData.title || data.title || 'GuestConnect';
    const options = {
        body: notificationData.body || data.body || 'You have a new notification',
        icon: data.icon || '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        vibrate: [200, 100, 200, 100, 200],
        data: data,
        tag: data.tag || 'guestconnect-' + Date.now(),
        requireInteraction: true, // Keep notification visible on Android
        renotify: true,
        silent: false,
        actions: [
            { action: 'open', title: 'Open', icon: '/static/images/icon-192.png' },
            { action: 'close', title: 'Dismiss' }
        ],
        image: data.image || null,
        timestamp: Date.now()
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    console.log('[Service Worker] Notification clicked:', event.action, event.notification.data);

    event.notification.close();

    if (event.action === 'close') {
        // User dismissed the notification
        return;
    }

    // Determine the URL to open
    const urlToOpen = new URL(
        event.notification.data?.url ||
        event.notification.data?.link ||
        '/dashboard/',
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

                // Then, try to find any window with the dashboard
                for (const client of clientList) {
                    if (client.url.includes('/dashboard') && 'focus' in client) {
                        // Navigate to the target URL and focus
                        return client.focus().then(() => {
                            return client.navigate(urlToOpen);
                        });
                    }
                }

                // No existing window found, open a new one
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
            .catch(error => {
                console.error('[Service Worker] Error handling notification click:', error);
                // Fallback: try to open window anyway
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', event => {
    console.log('[Service Worker] Sync event:', event.tag);
});
